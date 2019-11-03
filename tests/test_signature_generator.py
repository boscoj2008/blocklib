import unittest
from blocklib import generate_signatures


class TestPSig(unittest.TestCase):

    def test_feature_value(self):
        """Test signatures generated by feature-value."""
        attr_ind = [0, 1]
        dtuple = ('Joyce', 'Wang', 2134)
        signatures = [{'type': 'feature-value', 'columns': attr_ind, 'config': {}}]
        signatures = generate_signatures(signatures, dtuple)
        assert signatures == set(['JoyceWang'])

    def test_feature_value_substrings(self):
        """Test signatures generated by feature-value."""
        attr_ind = [0, 1]
        list_substrings_indices = [[1, 4], [6]]
        dtuple = ('Joyce', 'Wang', 2134)
        signatures = [{'type': 'feature-value', 'columns': attr_ind, 'config':
            {'list_substrings_indices': list_substrings_indices}}]
        signatures = generate_signatures(signatures, dtuple)
        assert signatures == {'oyc', 'ang'}

    def test_soundex(self):
        """Test signatures generated by soundex."""
        attr_ind = [0, 1]
        dtuple = ('Joyce', 'Wang', 2134)
        signature_strategies = [{'type': 'soundex', 'columns': attr_ind}]

        signatures = generate_signatures(signature_strategies, dtuple)
        assert signatures == {'W52', 'J2'}

    def test_n_gram(self):
        """Test signatures generated by n-gram."""
        attr_ind = [0, 1]
        dtuple = ('Joyce', 'Wang', 2134)

        # test 2-gram
        signatures = [
            {'type': 'n-gram', 'columns': attr_ind, 'config': {'n': 2}},
            {'type': 'n-gram', 'columns': attr_ind, 'config': {'n': 3}}
        ]
        signatures = generate_signatures(signatures, dtuple)
        res1 = {'Jo', 'oy', 'yc', 'ce', 'eW', 'Wa', 'an', 'ng'}
        res2 = {'Joy', 'oyc', 'yce', 'ceW', 'eWa', 'Wan', 'ang'}
        assert signatures == res1.union(res2)
