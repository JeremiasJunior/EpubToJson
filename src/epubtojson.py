from ebooklib import epub
from bs4 import BeautifulSoup
import os
import json
import mimetypes


class Epub:
    def __init__(self, file_path):
        self.book = epub.read_epub(file_path)
        self.version = '2.0'  # Fixed version since only EPUB 2.0 is supported

    def parse_toc_ncx(self):
        toc_file = self.book.get_item_with_id('ncx')
        
        if toc_file is None:
            raise FileNotFoundError("The toc.ncx file was not found in the EPUB. Please ensure the EPUB is properly formatted as EPUB 2.0.")
        
        soup = BeautifulSoup(toc_file.content, 'lxml')
        nav_points = soup.find_all('navpoint')
        chapters = []
        for point in nav_points:
            title = point.navlabel.text
            src = point.content['src']
            chapters.append((title, src))
        return chapters

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

    def get_chapters(self):
        chapters = self.parse_toc_ncx()
        chapter_data = {}
        for title, src in chapters:
            # Strip any leading/trailing whitespace or newline characters from the title
            clean_title = title.strip()
            chapter_content = self.extract_chapter_content(src)
            chapter_data[clean_title] = chapter_content
        return chapter_data
    
    def get_cover_image(self, output_path):
        # First, try to find the cover image by common IDs
        possible_ids = ['cover', 'cover-image']
        cover = None

        for cover_id in possible_ids:
            cover = self.book.get_item_with_id(cover_id)
            if cover:
                break

        # If no specific ID was found, explore other options
        if cover is None:
            for item in self.book.get_items():
                # Check if the item is an image
                if item.media_type and 'image' in item.media_type:
                    # Assuming the first image in the manifest might be the cover
                    cover = item
                    break

        # If a cover image is found, save it
        if cover:
            # Guess the file extension from the MIME type
            ext = mimetypes.guess_extension(cover.media_type)
            output_path_with_ext = os.path.splitext(output_path)[0] + ext

            with open(output_path_with_ext, 'wb') as f:
                f.write(cover.content)
            return output_path_with_ext
        else:
            raise FileNotFoundError("Cover image not found in the EPUB file.")

    def write_to_json(self, output_path):
        chapters = self.get_chapters()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=4)