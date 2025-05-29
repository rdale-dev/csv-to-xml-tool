import unittest
import xml.etree.ElementTree as ET
from xml_utils import create_element, escape_xml

class TestXmlElementCreation(unittest.TestCase):

    def test_create_element_with_text(self):
        parent = ET.Element("root")
        element = create_element(parent, "child", "Hello World")
        self.assertEqual(element.tag, "child")
        self.assertEqual(element.text, "Hello World")
        self.assertIs(parent.find("child"), element)

    def test_create_element_without_text(self):
        parent = ET.Element("root")
        element = create_element(parent, "child")
        self.assertEqual(element.tag, "child")
        self.assertIsNone(element.text)
        self.assertIs(parent.find("child"), element)

    def test_create_element_under_parent(self):
        root = ET.Element("root")
        parent_element = create_element(root, "parent")
        child_element = create_element(parent_element, "child", "Child Text")
        
        self.assertIs(root.find("parent"), parent_element)
        self.assertIs(parent_element.find("child"), child_element)
        self.assertEqual(child_element.text, "Child Text")

class TestXmlEscaping(unittest.TestCase):

    def test_escape_all_special_characters(self):
        self.assertEqual(escape_xml('&<>"\''), "&amp;&lt;&gt;&quot;&apos;")

    def test_escape_mixed_content(self):
        self.assertEqual(escape_xml('Test & "quotes" <tag>'), "Test &amp; &quot;quotes&quot; &lt;tag&gt;")

    def test_escape_no_special_characters(self):
        self.assertEqual(escape_xml("Hello World"), "Hello World")

    def test_escape_empty_string(self):
        self.assertEqual(escape_xml(""), "")

    def test_escape_none_input(self):
        self.assertEqual(escape_xml(None), "")

if __name__ == '__main__':
    unittest.main()
