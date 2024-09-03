from ebooklib import epub
from bs4 import BeautifulSoup
import json

class Epub:
    
    def __init__(self, file_path):
        self.book = epub.read_epub(file_path)
        self.version = self.detect_epub_version()

    def detect_epub_version(self):
        if 'toc.ncx' in [item.file_name for item in self.book.get_items()]:
            return '2.0'
        elif 'nav.xhtml' in [item.file_name for item in self.book.get_items()]:
            return '3.0'
        else:
            raise ValueError("Unsupported EPUB format")
        
    def get_nav_points(self):
        if self.version == '2.0':
            toc_file = self.book.get_item_with_id('toc.ncx')
            return self.parse_toc_ncx(toc_file)
        elif self.version == '3.0':
            nav_file = self.book.get_item_with_id('nav.xhtml')
            return self.parse_nav_xhtml(nav_file)

    def parse_toc_ncx(self, toc_file):
        soup = BeautifulSoup(toc_file.content, 'lxml')
        nav_points = soup.find_all('navpoint')
        chapters = []
        for point in nav_points:
            title = point.navlabel.text
            src = point.content['src']
            chapters.append((title, src))
        return chapters

    def parse_nav_xhtml(self, nav_file):
        soup = BeautifulSoup(nav_file.content, 'lxml')
        nav_points = soup.select('nav ol li a')
        chapters = []
        for point in nav_points:
            title = point.text
            src = point['href']
            chapters.append((title, src))
        return chapters
    
    def extract_chapter_content(self, src):
        content_item = self.book.get_item_with_href(src)
        soup = BeautifulSoup(content_item.content, 'lxml')
        return soup.get_text(separator='\n', strip=True)

    def get_chapters(self):
        chapters = self.get_nav_points()
        chapter_data = {}
        for title, src in chapters:
            chapter_content = self.extract_chapter_content(src)
            chapter_data[title] = chapter_content
        return chapter_data
    
    def extract_chapter_content(self, src):
        try:
            content_item = self.book.get_item_with_href(src)
            if content_item:
                soup = BeautifulSoup(content_item.content, 'lxml')
                return soup.get_text(separator='\n', strip=True)
            else:
                return "Content not found"
        except Exception as e:
            return f"Error extracting content: {e}"
    
    def write_to_json(self, output_path):
        chapters = self.get_chapters()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=4)
