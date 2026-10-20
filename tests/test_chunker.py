import unittest
from src.chunker import chunk_resume_by_section

class TestChunker(unittest.TestCase):
    def test_preserves_profile(self):
        chunks = chunk_resume_by_section('My intro\nEducation\nBTech\nProjects\nBuilt chatbot')
        self.assertEqual([c['section'] for c in chunks], ['Profile', 'Education', 'Projects'])

    def test_does_not_split_inline_heading(self):
        chunks = chunk_resume_by_section('I built Projects using Python')
        self.assertEqual(len(chunks), 1)

if __name__ == '__main__':
    unittest.main()
