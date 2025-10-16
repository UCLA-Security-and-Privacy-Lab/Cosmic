import re
from collections import defaultdict
from bs4 import BeautifulSoup

class PageInfo():

    def __init__(self, env_info):
        self.info = env_info
    
    def _parse_html(self, string):
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup
    def _normalize_xpath(self, xpath)->str:
        # Normalize by removing only numeric indices
        normalized_xpath = re.sub(r'\[\d+\]', '', xpath)
        return normalized_xpath

    def _group_xpaths(self, xpaths)->dict[list]:
        '''input: xpaths is xpath list [xpath1, xpath2]'''
        groups = defaultdict(list)
        
        # Map normalized paths to original paths
        for xpath in xpaths:
            normalized_xpath = self._normalize_xpath(xpath)
            groups[normalized_xpath].append(xpath)
        
        return groups
    
    def get_link_group(self)->dict[list]:
        return self._group_xpaths(self.info['xpaths_for_a_tags'])

    def _filter_outer_xpaths(self, xpath_dict)->dict:
        '''
            The XPath dict is dict {xpath: outerhtml}
        '''
        xpaths = sorted(list(xpath_dict.keys()), key=lambda x: x.count('/')) 
        outer_xpaths = []

        for xpath in xpaths:
            if not any(xpath.startswith(outer_xpath + '/') for outer_xpath in outer_xpaths):
                outer_xpaths.append(xpath)
        filtered_dict = {key: xpath_dict[key] for key in outer_xpaths}

        return filtered_dict
    
    # def get_elements_with_close_attr(self, xpath_dict):
    #     xpath_dict = self._filter_outer_xpaths(xpath_dict)
    #     for k,v in xpath_dict.items():
            