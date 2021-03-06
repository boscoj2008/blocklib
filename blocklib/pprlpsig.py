import statistics
from collections import defaultdict
from typing import Dict, List, Sequence, Any, Optional

import numpy as np

from .configuration import get_config
from .encoding import flip_bloom_filter
from .pprlindex import PPRLIndex
from .signature_generator import generate_signatures
from .stats import reversed_index_per_strategy_stats


class PPRLIndexPSignature(PPRLIndex):
    """Class that implements the PPRL indexing technique:

        Reference scalability entity resolution using probability signatures
        on parallel databases.

        This class includes an implementation of p-sig algorithm.
    """

    def __init__(self, config: Dict) -> None:
        """Initialize the class and set the required parameters.

        Arguments:
        - config: dict
            Configuration for P-Sig reverted index.

        """
        super().__init__()
        self.blocking_features = get_config(config, "blocking-features")
        self.filter_config = get_config(config, "filter")
        self.blocking_config = get_config(config, "blocking-filter")
        self.signature_strategies = get_config(config, 'signatureSpecs')
        self.rec_id_col = config.get("record-id-col", None)

    def build_reversed_index(self, data: Sequence[Sequence], verbose: bool = False, header: Optional[List[str]] = None):
        """Build inverted index given P-Sig method."""
        feature_to_index = self.get_feature_to_index_map(data, header)
        self.set_blocking_features_index(self.blocking_features, feature_to_index)

        # Build index of records
        if self.rec_id_col is None:
            record_ids = np.arange(len(data))
        else:
            record_ids = [x[self.rec_id_col] for x in data]

        reversed_index_per_strategy = \
            [defaultdict(list) for _ in range(len(self.signature_strategies))]  # type: List[Dict[str, List[Any]]]
        # Build inverted index
        # {signature -> record ids}
        for rec_id, dtuple in zip(record_ids, data):

            signatures = generate_signatures(self.signature_strategies, dtuple, feature_to_index)

            for i, signature in enumerate(signatures):
                reversed_index_per_strategy[i][signature].append(rec_id)

        n = len(data)
        reversed_index_per_strategy = [self.filter_reversed_index(data, reversed_index) for reversed_index in
                                       reversed_index_per_strategy]
        if verbose:
            strat_stats = reversed_index_per_strategy_stats(reversed_index_per_strategy, n)
            print("Statistics for the individual strategies:")
            for strat_stat in strat_stats:
                print('Strategy {}:'.format(strat_stat["strategy_idx"]))
                print('\tblock size {} min, {} max, {:.2f} avg, {} median, {:.2f} std'
                      .format(strat_stat["min_size"], strat_stat["max_size"], strat_stat["avg_size"],
                              strat_stat["med_size"], strat_stat["std_size"]))
                print('\t {} blocks, {} filtered elements, {:.2f}% coverage'
                      .format(strat_stat["num_of_blocks"], strat_stat["num_filtered_elements"],
                              (strat_stat["coverage"] * 100)))

        # combine the reversed indices into one
        filtered_reversed_index = reversed_index_per_strategy[0]
        for rev_idx in reversed_index_per_strategy[1:]:
            filtered_reversed_index.update(rev_idx)

        # check if final inverted index is empty
        if len(filtered_reversed_index) == 0:
            raise ValueError('P-Sig: All records are filtered out!')

        # compute coverage information
        entities = set()
        for recids in filtered_reversed_index.values():
            for rid in recids:
                entities.add(rid)
        coverage = round(len(entities) / len(record_ids) * 100, 2)
        if coverage == 100:
            print('P-Sig: {}% records are covered in blocks'.format(coverage))
        else:
            print('P-Sig: Warning! only {}% records are covered in blocks. Please consider to improve signatures'
                  .format(coverage))

        # map signatures in reversed_index into bloom filter
        num_hash_func = int(self.blocking_config.get("number-hash-functions", None))
        bf_len = int(self.blocking_config.get("bf-len", None))

        reversed_index = {}  # type: Dict[str, List[Any]]

        for signature, rec_ids in filtered_reversed_index.items():
            bf_set = str(tuple(flip_bloom_filter(signature, bf_len, num_hash_func)))
            if bf_set in reversed_index:
                reversed_index[bf_set].extend(rec_ids)
            else:
                reversed_index[bf_set] = rec_ids

        return reversed_index

    def filter_reversed_index(self, data: Sequence[Sequence], reversed_index: Dict):
        # Filter inverted index based on ratio
        n = len(data)

        # filter blocks based on filter type
        filter_type = get_config(self.filter_config, "type")
        if filter_type == "ratio":
            min_occur_ratio = get_config(self.filter_config, 'min')
            max_occur_ratio = get_config(self.filter_config, 'max')
            reversed_index = {k: v for k, v in reversed_index.items() if n * max_occur_ratio > len(v) > n * min_occur_ratio}
        elif filter_type == "count":
            min_occur_count = get_config(self.filter_config, "min")
            max_occur_count = get_config(self.filter_config, "max")
            reversed_index = {k: v for k, v in reversed_index.items() if max_occur_count > len(v) > min_occur_count}
        else:
            raise NotImplementedError("Don't support {} filter yet.".format(filter_type))

        return reversed_index
