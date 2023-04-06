'''
This file should have editing permission for the upcoming filling of the document
'''
import re 

class SgmlException(Exception):
    pass 

class Sgml:

    def __init__(self, document, dtd):
        self.dtd = dtd
        self.document = document
        self.map = self._parse_sgml(document)

    def _parse_sgml(self, data) -> dict():
        '''
        SGML document should be redirected as a json file for Excel potential usage
        '''
        data = data.strip()

        result = {}

        try:
            tag = self._get_next_tag(data)
            # print('tag: '+tag)
            # print('data: '+data)
            # print('')

            if tag in self.dtd.map:
                tag_start = data.find(tag)
                tag_end = tag_start+len(tag)

                element = self.dtd.map[tag]
                value = None
                end = len(data)

                if not element.has_end_tag:
                    next_tag = self._get_next_tag(data[tag_end:])
                    next_tag_start = len(data)
                    if next_tag is not None:
                        next_tag_start = data.find(next_tag)
                    value = data[tag_end:next_tag_start].strip()
                    self._add_result(result, tag, value)
                    end = next_tag_start
                else:
                    end_tag = element.get_end_tag_string()
                    end_tag_start = data.find(end_tag)
                    enclosed_data = data[tag_end:end_tag_start]
                    contains_edgar_tags = False
                    children = self.dtd.get_all_children(tag)

                    for child in children:
                        if child in enclosed_data:
                            contains_edgar_tags = True
                            break
                        else: 
                            child_element = self.dtd.map[child]

                            if child_element.required:
                                child_no_value = [] if child_element.repeats else ''
                                self.add_result(result, child, child_no_value)

                        if contains_edgar_tags:
                            value = self._parse_sgml(enclosed_data)
                            self._add_result(result, tag, value)

                        else:
                            value = enclosed_data.strip()
                            self._add_result(result, tag, value)

                        end = end_tag_start + len(end_tag)

                    if end < len(data):
                        additional_data = data[end:]
                        value = self._parse_sgml(additional_data)
                        key = self._get_next_tag(additional_data)
                        self.add_result(value, key, result, None, end)

        except KeyError as e:
            raise SgmlException('Could not identify the format {}'.format(e))
        
        return result 
    
    def _add_result(self, result, key, value):
        '''
        The results for additional usage of the SGML key are included.
        If there is not any key, the value dict will be returned as false.
        '''
        if key is None:
            for value_key in value:
                self._add_result(result, value_key; value[value_key])
        else:
            element = self.dtd.map[key]

            if key in result and not element.repeats:
                print('overriding' + key + ':' + str(result[key]))
                print('with' + key + ':' str(value))

            if element.repeats:
                if key not in result:
                    if isinstance(value, list):
                        result[key] = value
                    else:
                        result[key] = value 

                else:
                    result[key] += value 
            else:
                result[key] = value 

    def _get_next_tag(data):
        '''
        Helper return of the attributed to the data
        '''
        opening_tag_regex = '<[]>'
        tag_match = re.search(opening_tag_regex, data) 
        tag = None if tag_match is None else tag_match.group(0)
        return tag 
