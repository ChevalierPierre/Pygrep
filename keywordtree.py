from sys import argv


class State(object):
    __slots__ = ['identifier', 'symbol', 'success', 'transitions', 'parent',
                 'matched_keyword', 'longest_strict_suffix']

    def __init__(self, identifier, symbol=None, parent=None, success=False):
        self.symbol = symbol
        self.identifier = identifier
        self.transitions = {}
        self.parent = parent
        self.success = success
        self.matched_keyword = None
        self.longest_strict_suffix = None

class KeywordTree(object):

    def __init__(self, case_insensitive=False):
        '''
        @param case_insensitive: If true, case will be ignored when searching.
                                 Setting this to true will have a positive
                                 impact on performance.
                                 Defaults to false.
        '''
        self._zero_state = State(0)
        self._counter = 1
        self._finalized = False
        self._case_insensitive = case_insensitive

    def add(self, keyword):
        '''
        Add a keyword to the tree.
        Can only be used before finalize() has been called.
        Keyword should be str or unicode.
        '''
        if self._finalized:
            raise ValueError('KeywordTree has been finalized.' +
                             ' No more keyword additions allowed')
        original_keyword = keyword
        if self._case_insensitive:
            keyword = keyword.lower()
        if len(keyword) <= 0:
            return
        current_state = self._zero_state
        for char in keyword:
            try:
                current_state = current_state.transitions[char]
            except KeyError:
                next_state = State(self._counter, parent=current_state,
                                   symbol=char)
                self._counter += 1
                current_state.transitions[char] = next_state
                current_state = next_state
        current_state.success = True
        current_state.matched_keyword = original_keyword

    def search_all(self, text):
        '''
        Search a text for all occurences of the added keywords.
        Can only be called after finalized() has been called.
        O(n) with n = len(text)
        @return: List used to iterate over the results.
                 Or None if no keyword was found in the text.
        '''
        if not self._finalized:
            raise ValueError('KeywordTree has not been finalized.' +
                             ' No search allowed. Call finalize() first.')
        if self._case_insensitive:
            text = text.lower()
        zero_state = self._zero_state
        current_state = zero_state
        ret=[]
        for idx, symbol in enumerate(text):
            current_state = current_state.transitions.get(
                symbol, zero_state.transitions.get(symbol, zero_state))
            state = current_state
            while state is not zero_state:
                if state.success:
                    keyword = state.matched_keyword
                    ret.append(keyword)
                state = state.longest_strict_suffix
        return ret

    def finalize(self):
        '''
        Needs to be called after all keywords have been added and
        before any searching is performed.
        '''
        if self._finalized:
            raise ValueError('KeywordTree has already been finalized.')
        self._zero_state.longest_strict_suffix = self._zero_state
        self.search_lss_for_children(self._zero_state)
        self._finalized = True

    def search_lss_for_children(self, zero_state):
        processed = set()
        to_process = [zero_state]
        while to_process:
            state = to_process.pop()
            processed.add(state.identifier)
            for child in state.transitions.values():
                if child.identifier not in processed:
                    self.search_lss(child)
                    to_process.append(child)

    def search_lss(self, state):
        zero_state = self._zero_state
        parent = state.parent
        traversed = parent.longest_strict_suffix
        while True:
            if state.symbol in traversed.transitions and \
                    traversed.transitions[state.symbol] is not state:
                state.longest_strict_suffix = \
                    traversed.transitions[state.symbol]
                break
            elif traversed is zero_state:
                state.longest_strict_suffix = zero_state
                break
            else:
                traversed = traversed.longest_strict_suffix
        suffix = state.longest_strict_suffix
        if suffix is zero_state:
            return
        if suffix.longest_strict_suffix is None:
            self.search_lss(suffix)
        for symbol, next_state in suffix.transitions.items():
            if symbol not in state.transitions:
                state.transitions[symbol] = next_state


def readme():
    print(
        """\nThis script tells you in which lines you can find keywords:\n\t- It takes a file name as first input which will be used to find the keywords in it.\n\t- A 'true' or 'false' boolean as second input to define if case sensitive.\n\t- An 'and' or 'or' connector to choose wether you want all the keywords present in a line or any of the keywords.\n\t- The last inputs will be the keywords you want to find the line of in the text file.\n""")


def main():
    args = len(argv)
    if args < 6 or argv[2] not in ['true', 'false'] or argv[3] not in ['and', 'or']:
        return readme()
    kw = argv[4:]
    try:
        filestream = open(argv[1], 'r')
        filelines = filestream.readlines()
        filestream.close()
    except ValueError:
        raise ValueError('File error')
    kwtree = KeywordTree(case_insensitive=True) if argv[2] == 'false' else KeywordTree()
    for i in range(2, args):
        kwtree.add(argv[i])
    kwtree.finalize()
    ret = []
    for i in range(len(filelines)):
        result = kwtree.search_all(filelines[i])
        if argv[3] == 'and':
            if all(elem in result for elem in kw):
                ret.append(i + 1)
        else:
            if any(elem in result for elem in kw):
                ret.append(i + 1)
    print(ret)



if __name__ == '__main__':
    main()
