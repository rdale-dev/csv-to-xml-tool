import unittest
from datetime import datetime # For testing date outputs if needed, though format_date handles strings
from data_cleaning import format_date, standardize_state_name, map_value

class TestFormatDate(unittest.TestCase):

    def test_format_date_valid_various_formats(self):
        self.assertEqual(format_date("2023-10-26"), "2023-10-26")
        self.assertEqual(format_date("10/26/2023"), "2023-10-26")
        self.assertEqual(format_date("10-26-2023"), "2023-10-26")
        self.assertEqual(format_date("10/26/23"), "2023-10-26")
        self.assertEqual(format_date("2023/10/26"), "2023-10-26") # Added based on default formats
        self.assertEqual(format_date("23/10/26", input_formats=['%y/%m/%d']), "2023-10-26") # Test specific format

    def test_format_date_custom_input_formats(self):
        self.assertEqual(format_date("26.10.2023", input_formats=["%d.%m.%Y"]), "2023-10-26")
        self.assertEqual(format_date("20231026", input_formats=["%Y%m%d"]), "2023-10-26")
        # Test with a list, first one fails, second one passes
        self.assertEqual(format_date("26/Oct/2023", input_formats=["%d/%m/%Y", "%d/%b/%Y"]), "2023-10-26")

    def test_format_date_invalid_strings(self):
        self.assertEqual(format_date("invalid-date"), "") # Default default_return
        self.assertEqual(format_date("2023-13-01"), "") # Invalid month
        self.assertEqual(format_date("10/32/2023"), "") # Invalid day
        self.assertEqual(format_date("20231026", input_formats=["%d-%m-%Y"]), "") # Mismatch format

    def test_format_date_empty_and_none_input(self):
        self.assertEqual(format_date(""), "")
        self.assertEqual(format_date(None), "")
        self.assertEqual(format_date("   "), "") # Whitespace only
        self.assertEqual(format_date("", default_return="N/A"), "N/A")
        self.assertEqual(format_date(None, default_return="MISSING"), "MISSING")

    def test_format_date_output_format_and_default(self):
        self.assertEqual(format_date("1/1/2023"), "2023-01-01") # Check zero padding
        self.assertEqual(format_date("2023-1-1"), "2023-01-01") # Check zero padding
        self.assertEqual(format_date("bad", default_return="---"), "---")

class TestStandardizeStateName(unittest.TestCase):
    # Using DEFAULT_VALID_STATES from data_cleaning for some tests
    # These are the states the function itself knows about if no list is passed
    DEFAULT_STATE_MAPPINGS = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
        'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
        'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina',
        'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
        'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
        'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
        'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
        'AS': 'American Samoa', 'GU': 'Guam', 'MP': 'Northern Mariana Islands', 'PR': 'Puerto Rico',
        'VI': 'U.S. Virgin Islands'
    }
    DEFAULT_VALID_STATES_LIST = set(DEFAULT_STATE_MAPPINGS.values()) | {
        "Armed Forces Europe", "Armed Forces Pacific", "Armed Forces the Americas",
        "Federated States of Micronesia", "Marshall Islands", "Republic of Palau",
        "United States Minor Outlying Islands"
    }


    def test_standardize_state_abbreviations_and_names_mixed_case(self):
        self.assertEqual(standardize_state_name("AL"), "Alabama")
        self.assertEqual(standardize_state_name("al"), "Alabama")
        self.assertEqual(standardize_state_name("Alabama"), "Alabama")
        self.assertEqual(standardize_state_name("alabama"), "Alabama")
        self.assertEqual(standardize_state_name(" Al "), "Alabama")
        self.assertEqual(standardize_state_name("iOwA"), "Iowa")
        self.assertEqual(standardize_state_name("District of Columbia"), "District of Columbia")
        self.assertEqual(standardize_state_name("d.c."), "District of Columbia") # Assuming 'd.c.' maps to DC

    def test_standardize_state_invalid_names(self):
        self.assertEqual(standardize_state_name("UnknownState"), "UnknownState") # Returns original if not in map and no valid_list
        self.assertEqual(standardize_state_name("XX"), "XX") 
        self.assertEqual(standardize_state_name("Not A State", default_return="INVALID"), "INVALID")

    def test_standardize_state_empty_and_none(self):
        self.assertEqual(standardize_state_name(""), "")
        self.assertEqual(standardize_state_name(None), "")
        self.assertEqual(standardize_state_name("   "), "")
        self.assertEqual(standardize_state_name("", default_return="EMPTY"), "EMPTY")

    def test_standardize_state_with_valid_states_list_pass(self):
        valid_list = {"California", "New York", "Texas"}
        self.assertEqual(standardize_state_name("CA", valid_states_list=valid_list), "California")
        self.assertEqual(standardize_state_name("New York", valid_states_list=valid_list), "New York")
        self.assertEqual(standardize_state_name("texas", valid_states_list=valid_list), "Texas")

    def test_standardize_state_with_valid_states_list_fail(self):
        valid_list = {"California", "New York", "Texas"}
        # Standardizes to "Florida", but "Florida" is not in valid_list
        self.assertEqual(standardize_state_name("FL", valid_states_list=valid_list, default_return="NOT_VALID"), "NOT_VALID")
        # "Unknown" is not in any mapping, and not in valid_list
        self.assertEqual(standardize_state_name("Unknown", valid_states_list=valid_list, default_return="NOT_VALID"), "NOT_VALID")
        # Standardizes to "Alabama", then checks against valid_list. "Alabama" is not in valid_list.
        self.assertEqual(standardize_state_name("al", valid_states_list=valid_list, default_return="FAIL"), "FAIL")


    def test_standardize_state_honors_default_return(self):
        self.assertEqual(standardize_state_name("XYZ", default_return="UNKNOWN_STATE"), "UNKNOWN_STATE")
        self.assertEqual(standardize_state_name("", default_return="EMPTY_STATE"), "EMPTY_STATE")
        valid_list = {"California"}
        self.assertEqual(standardize_state_name("NY", valid_states_list=valid_list, default_return="INVALID_NY"), "INVALID_NY")

    def test_standardize_state_with_comprehensive_default_list(self):
        # Test against the function's own default list of valid states if valid_states_list is None
        self.assertEqual(standardize_state_name("Armed Forces Europe"), "Armed Forces Europe")
        self.assertEqual(standardize_state_name("armed forces pacific", valid_states_list=self.DEFAULT_VALID_STATES_LIST), "Armed Forces Pacific")
        # This should fail if not in the default internal list and no override provided
        self.assertEqual(standardize_state_name("NonExistentArmedForces", valid_states_list=self.DEFAULT_VALID_STATES_LIST, default_return="NOT_FOUND"), "NOT_FOUND")


class TestMapValue(unittest.TestCase):
    mapping = {"apple": "FRUIT", "banana": "FRUIT", "carrot": "VEGETABLE", 123: "NUMBER"}
    default = "UNKNOWN"

    def test_map_value_successful_mapping_case_sensitive(self):
        self.assertEqual(map_value("apple", self.mapping, self.default, case_sensitive=True), "FRUIT")
        self.assertEqual(map_value(123, self.mapping, self.default, case_sensitive=True), "NUMBER")

    def test_map_value_fail_case_sensitive(self):
        self.assertEqual(map_value("Apple", self.mapping, self.default, case_sensitive=True), self.default)

    def test_map_value_successful_mapping_case_insensitive(self):
        self.assertEqual(map_value("Apple", self.mapping, self.default, case_sensitive=False), "FRUIT")
        self.assertEqual(map_value("CARROT", self.mapping, self.default, case_sensitive=False), "VEGETABLE")
        # Numeric keys are typically matched exactly or by string form if not careful
        self.assertEqual(map_value("123", self.mapping, self.default, case_sensitive=False), "NUMBER")


    def test_map_value_not_in_mapping_dict(self):
        self.assertEqual(map_value("grape", self.mapping, self.default), self.default)
        self.assertEqual(map_value(999, self.mapping, self.default), self.default)

    def test_map_value_none_or_empty_input(self):
        self.assertEqual(map_value(None, self.mapping, self.default), self.default)
        self.assertEqual(map_value("", self.mapping, self.default), self.default)
        self.assertEqual(map_value("  ", self.mapping, self.default), self.default)
        self.assertEqual(map_value(None, self.mapping, "SPEC_DEFAULT"), "SPEC_DEFAULT")


if __name__ == '__main__':
    unittest.main()
