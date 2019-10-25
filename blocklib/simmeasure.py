"""Similarity Measure Algorithms."""
import hashlib
from blocklib.configuration import get_config

class SimMeasure:
  """General class that implements similarity measures.
  """

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

  def __init__(self):
    """Initialisation, noting to do.
    """

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

  def sim(self, s1, s2, do_cache=False):
    """Calculate and return the similarity between two strings (a value
       between 0 and 1).

       If this similarity should be cached set the argument do_cache to True.
    """

# ----------------------------------------------------------------------------

class EditSim(SimMeasure):
    """Class that implements Edit (or Levenshtein) distance for two strings."""

    def __init__(self, config):
        """Initialize instance."""
        if 'min_threshold' in config:
            self.min_threshold = config['min_threshold']
        else:
            self.min_threshold = None

    def sim(self, str1, str2):
        """Return sim score between 0 to 1."""
        min_threshold = self.min_threshold
        # Quick check if the strings are empty or the same - - - - - - - - - - - - -
        #
        if (str1 == '') or (str2 == ''):
            return 0.0
        elif (str1 == str2):
            return 1.0

        n = len(str1)
        m = len(str2)
        max_len = max(n,m)

        if (min_threshold != None):
            if (isinstance(min_threshold, float)) and (min_threshold > 0.0) and \
               (min_threshold > 0.0):

                len_diff = abs(n-m)
                w = 1.0 - float(len_diff) / float(max_len)

                if (w  < min_threshold):
                    return 0.0  # Similariy is smaller than minimum threshold

                else: # Calculate the maximum distance possible with this threshold
                    max_dist = (1.0-min_threshold)*max_len

            else:
              logging.exception('Illegal value for minimum threshold (not between' + \
                              ' 0 and 1): %f' % (min_threshold))
              raise Exception

        if (n > m):  # Make sure n <= m, to use O(min(n,m)) space
            str1, str2 = str2, str1
            n, m =       m, n

        current = list(range(n+1))

        for i in range(1, m+1):

            previous = current
            current =  [i]+n*[0]
            str2char = str2[i-1]

            for j in range(1,n+1):
              substitute = previous[j-1]
              if (str1[j-1] != str2char):
                substitute += 1

              # Get minimum of insert, delete and substitute
              #
              current[j] = min(previous[j]+1, current[j-1]+1, substitute)

            if (min_threshold != None) and (min(current) > max_dist):
              return 1.0 - float(max_dist+1) / float(max_len)

        w = 1.0 - float(current[n]) / float(max_len)
        return w


class DiceSim(SimMeasure):
  """Class that implements the Dice coefficient for the two input strings.
     This methods uses the constants: ngram_len and ngram_padding (and if this
     constant is set to True also padding_start_char and self.padding_end_char).

     If the argument do_cache is set to True then the generated q-gram lists
     will be stored in a dictionary to prevent their repeated computation.
  """

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

  def __init__(self, config):
    """Initialise the cache."""
    self.ngram_len = int(get_config(config, 'ngram_len'))
    self.ngram_padding = get_config(config, 'ngram_padding')
    self.padding_start_char = get_config(config, 'padding_start_char')
    self.padding_end_char = get_config(config, 'padding_end_char')
    self.q_gram_cache = {}  # Store strings converted into q-grams. Keys in
                            # this will be strings and their values their
                            # q-gram list
    self.sim_cache = {}     # Store the string pair and its similarity in a
                            # cache as well

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

  def sim(self, s1, s2, do_cache=False):
    """Calculate the similarity between the given two strings. The method
       returns a value between 0.0 and 1.0.

       If this similarity should be cached set the argument do_cache to True.
    """

    assert do_cache in [True, False]

    if (s1 == s2):  # Quick check for equality
      return 1.0

    # Check if the string pair has been compared before
    #
    if ((s1,s2) in self.sim_cache):
      return self.sim_cache[(s1,s2)]

    q_minus_1 = self.ngram_len - 1

    # Convert input strings into q-gram lists
    #
    if (do_cache == True) and (s1 in self.q_gram_cache):
      l1 = self.q_gram_cache[s1]

    else:  # Need to calculate q-gram list for the first string
      if (self.ngram_padding == True):
        ps1 = self.padding_start_char*q_minus_1 + s1 + self.padding_end_char*q_minus_1
      else:
        ps1 = s1

      l1 = [ps1[i:i+self.ngram_len] for i in range(len(ps1) - q_minus_1)]

      if (do_cache == True):
        self.q_gram_cache[s1] = l1

    if (do_cache == True) and (s2 in self.q_gram_cache):
      l2 = self.q_gram_cache[s2]

    else:  # Need to calculate q-gram list for the second string
      if (self.ngram_padding == True):
        ps2 = self.padding_start_char*q_minus_1 + s2 + self.padding_end_char*q_minus_1
      else:
        ps2 = s2

      l2 = [ps2[i:i+self.ngram_len] for i in range(len(ps2) - q_minus_1)]

      if (do_cache == True):
        self.q_gram_cache[s2] = l2

    common = len(set(l1).intersection(set(l2)))

    sim = 2.0*common / (len(l1)+len(l2))

    if (do_cache == True):
      self.sim_cache[(s1,s2)] = sim

    return sim

# ----------------------------------------------------------------------------
