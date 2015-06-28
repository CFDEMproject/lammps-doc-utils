# Python rewrite of txt2html by Richard Berger (2015)
# The original txt2html was written in C by Steve Plimpton (http://www.cs.sandia.gov/cgi-bin/sjplimp/)
import os
import re
import sys
import argparse

class Markup(object):
    BOLD_START = "["
    BOLD_END = "]"
    ITALIC_START = "{"
    ITALIC_END = "}"
    START_PLACEHOLDER = "<<PLACEHOLDER>>"
    END_PLACEHOLDER = "<</PLACEHOLDER>>"
    PUNCTUATION_CHARACTERS = '.,;:?!()'

    def __init__(self):
        link_regex = r"(?P<text>[^\"]+)\"_(?P<link>[^\s\t\n]+)"
        self.link_pattern = re.compile(link_regex)
        self.aliases = {}

    def convert(self, text):
        text = self.bold(text)
        text = self.italic(text)
        text = self.link(text)
        return text

    def add_link_alias(self, name, href):
        self.aliases[name] = href

    def bold(self, text):
        text = text.replace("\\" + Markup.BOLD_START, Markup.START_PLACEHOLDER)
        text = text.replace("\\" + Markup.BOLD_END, Markup.END_PLACEHOLDER)
        text = text.replace(Markup.BOLD_START, "<B>")
        text = text.replace(Markup.BOLD_END, "</B>")
        text = text.replace(Markup.START_PLACEHOLDER, Markup.BOLD_START)
        text = text.replace(Markup.END_PLACEHOLDER, Markup.BOLD_END)
        return text

    def italic(self, text):
        text = text.replace("\\" + Markup.ITALIC_START, Markup.START_PLACEHOLDER)
        text = text.replace("\\" + Markup.ITALIC_END, Markup.END_PLACEHOLDER)
        text = text.replace(Markup.ITALIC_START, "<I>")
        text = text.replace(Markup.ITALIC_END, "</I>")
        text = text.replace(Markup.START_PLACEHOLDER, Markup.ITALIC_START)
        text = text.replace(Markup.END_PLACEHOLDER, Markup.ITALIC_END)
        return text

    def link(self, text):
        for name, link in self.link_pattern.findall(text):
            link = link.rstrip(Markup.PUNCTUATION_CHARACTERS)

            if link in self.aliases:
                href = self.aliases[link]
            else:
                href = link

            href = "<A HREF = \"" + href + "\">" + name + "</A>"
            text = text.replace('\"%s\"_%s' % (name, link), href, 1)
        return text

class Formatting(object):
    def __init__(self, markup):
        image_regex = r"^image\((?P<file>[^\,]+)(,(?P<link>[^\,]+))?\)"
        named_link_regex = r"^link\((?P<name>[^\,]+)\)"
        define_link_alias_regex = r"^link\((?P<alias>[^\,]+),(?P<value>[^\,]+)\)"
        self.image_pattern = re.compile(image_regex)
        self.named_link_pattern = re.compile(named_link_regex)
        self.define_link_alias_pattern = re.compile(define_link_alias_regex)
        self.markup = markup
        self.first_header = ""

    def convert(self, command, paragraph):
        if command == "p":
            return self.paragraph(paragraph)
        elif command == "b":
            return self.linebreak(paragraph)
        elif command == "pre":
            return self.preformat(paragraph)
        elif command == "c":
            return self.center(paragraph)
        elif command == "h1" or command == "h2" or command == "h3" or \
                        command == "h4" or command == "h5" or command == "h6":
            level = int(command[1])
            return self.header(paragraph, level)
        elif command == "ul":
            return self.unordered_list(paragraph)
        elif command == "ol":
            return self.ordered_list(paragraph)
        elif command == "dl":
            return self.definition_list(paragraph)
        elif command == "l":
            return self.list_item(paragraph)
        elif command == "dt":
            return self.definition_term(paragraph)
        elif command == "dd":
            return self.definition_description(paragraph)
        elif command == "ulb":
            return self.unordered_list_begin(paragraph)
        elif command == "ule":
            return self.unordered_list_end(paragraph)
        elif command == "olb":
            return self.ordered_list_begin(paragraph)
        elif command == "ole":
            return self.ordered_list_end(paragraph)
        elif command == "dlb":
            return self.definition_list_begin(paragraph)
        elif command == "dle":
            return self.definition_list_end(paragraph)
        elif command == "all(p)":
            return self.all_paragraphs(paragraph)
        elif command == "all(c)":
            return self.all_centered(paragraph)
        elif command == "all(b)":
            return self.all_breaks(paragraph)
        elif command == "all(l)":
            return self.all_list_items(paragraph)
        elif command == "line":
            return self.horizontal_rule(paragraph)
        elif command.startswith("image"):
            m = self.image_pattern.match(command)
            return self.image(paragraph, file=m.group('file'), link=m.group('link'))
        elif command.startswith("link"):
            m = self.named_link_pattern.match(command)
            if m:
                return self.named_link(paragraph, name=m.group('name'))
            m2 = self.define_link_alias_pattern.match(command)
            if m2:
                return self.define_link_alias(paragraph, alias=m2.group('alias'), value=m2.group('value'))
        elif command.startswith("tb"):
            configuration = self.get_table_configuration(command)
            return self.table(paragraph, configuration)
        return ""

    def paragraph(self, paragraph):
        return "<P>" + paragraph + "</P>"

    def linebreak(self, paragraph):
        return paragraph + "<BR>"

    def preformat(self, paragraph):
        return "<PRE>" + paragraph + "</PRE>"

    def center(self, paragraph):
        return "<CENTER>" + paragraph + "</CENTER>"

    def header(self, paragraph, level):
        if self.first_header == "":
            self.first_header = paragraph.strip()
        return "<H%d>%s</H%d>" % (level, paragraph, level)

    def unordered_list(self, paragraph):
        converted = "<UL>"
        for line in paragraph.splitlines():
            converted += "<LI>" + line + "\n"
        converted += "</UL>"
        return converted

    def ordered_list(self, paragraph):
        converted = "<OL>"
        for line in paragraph.splitlines():
            converted += "<LI>" + line + "\n"
        converted += "</OL>"
        return converted

    def definition_list(self, paragraph):
        converted = "<DL>"
        is_title = True
        for line in paragraph.splitlines():
            if is_title:
                converted += "<DT>" + line + "\n"
            else:
                converted += "<DD>" + line + "\n"

            is_title = not is_title

        converted += "</DL>"
        return converted

    def list_item(self, paragraph):
        return "<LI>" + paragraph

    def definition_term(self, paragraph):
        return "<DT>" + paragraph

    def definition_description(self, paragraph):
        return "<DD>" + paragraph

    def unordered_list_begin(self, paragraph):
        return "<UL>" + paragraph

    def unordered_list_end(self, paragraph):
        return paragraph + "</UL>"

    def ordered_list_begin(self, paragraph):
        return "<OL>" + paragraph

    def ordered_list_end(self, paragraph):
        return paragraph + "</OL>"

    def definition_list_begin(self, paragraph):
        return "<DL>" + paragraph

    def definition_list_end(self, paragraph):
        return paragraph + "</DL>"

    def all_paragraphs(self, paragraph):
        converted = ""
        for line in paragraph.splitlines():
            converted += "<P>" + line + "</P>\n"
        return converted

    def all_centered(self, paragraph):
        converted = ""
        for line in paragraph.splitlines():
            converted += "<CENTER>" + line + "</CENTER>\n"
        return converted

    def all_breaks(self, paragraph):
        return paragraph.replace("\n", "<BR>\n")

    def all_list_items(self, paragraph):
        converted = ""
        for line in paragraph.splitlines():
            converted += "<LI>" + line + "\n"
        return converted

    def horizontal_rule(self, paragraph):
        return "<HR>" + paragraph

    def image(self, paragraph, file, link=None):
        converted = "<IMG SRC = \"" + file + "\">"
        if link:
            converted = "<A HREF = \"" + link + "\">" + converted + "</A>"
        return converted + paragraph

    def named_link(self, paragraph, name):
        return "<A NAME = \"" + name + "\"></A>" + paragraph

    def define_link_alias(self, paragraph, alias, value):
        self.markup.add_link_alias(alias, value)
        return paragraph

    def get_table_configuration(self, command):
        config = {
            'separator': ',',
            'num_columns': 0,
            'border_width': 1,
            'table_alignment': 'center'
        }

        table_regex = r"^tb\((?P<configuration>.+)\)"
        table_pattern = re.compile(table_regex)

        m = table_pattern.match(command)
        if m:
            entries = m.groups('configuration')[0].split(',')
            alignments = {'l': 'left', 'c': 'center', 'r' : 'right'}
            vertical_alignments = {'t': 'top', 'm': 'middle', 'ba' : 'baseline', 'bo': 'bottom'}

            for entry in entries:
                lhs, rhs = entry.split('=')

                if lhs == 'c':
                    config['num_columns'] = int(rhs)
                elif lhs == 's':
                    config['separator'] = rhs
                elif lhs == 'b':
                    config['border_width'] = int(rhs)
                elif lhs == 'w':
                    if rhs.endswith("%"):
                        config['table_width'] = rhs
                    else:
                        config['cell_width'] = rhs
                elif lhs == "a":
                    config['table_alignment'] = alignments[rhs]
                elif lhs == "ea":
                    config['cell_alignment'] = alignments[rhs]
                elif lhs == "eva":
                    config['cell_vertical_alignment'] = vertical_alignments[rhs]
                elif lhs.startswith("cw") and len(lhs) >= 3:
                    column = int(lhs[2:]) - 1
                    if 'custom_cell_width' not in config:
                        config['custom_cell_width'] = {}
                    config['custom_cell_width'][column] = rhs
                elif lhs.startswith("ca") and len(lhs) >= 3:
                    column = int(lhs[2:]) - 1
                    if 'custom_cell_alignment' not in config:
                        config['custom_cell_alignment'] = {}
                    config['custom_cell_alignment'][column] = alignments[rhs]

        return config

    def table(self, paragraph, configuration):
        if configuration['num_columns'] == 0:
            rows = self.create_table_with_columns_based_on_newlines(paragraph, configuration['separator'])
        else:
            rows = self.create_table_with_fixed_number_of_columns(paragraph, configuration['separator'],
                                                                  configuration['num_columns'])

        tbl = "<DIV ALIGN=%s>" % configuration['table_alignment']
        tbl += "<TABLE  "

        if 'table_width' in configuration:
            tbl += "WIDTH=\"%s\" " % configuration['table_width']

        tbl += "BORDER=%d >\n" % configuration['border_width']

        for row_idx in range(len(rows)):
            columns = rows[row_idx]
            tbl += "<TR"

            if 'cell_alignment' in configuration:
                tbl += " ALIGN=\"%s\"" % configuration['cell_alignment']

            if 'cell_vertical_alignment' in configuration:
                tbl += " VALIGN =\"%s\"" % configuration['cell_vertical_alignment']

            tbl += ">"

            for col_idx in range(len(columns)):
                col = columns[col_idx]
                tbl += "<TD "

                if 'custom_cell_width' in configuration:
                    if col_idx in configuration['custom_cell_width']:
                        tbl += "WIDTH=\"%s\"" % configuration['custom_cell_width'][col_idx]
                else:
                    if 'cell_width' in configuration:
                        tbl += "WIDTH=\"%s\"" % configuration['cell_width']

                if 'custom_cell_alignment' in configuration:
                    if col_idx in configuration['custom_cell_alignment']:
                        tbl += " ALIGN =\"%s\"" % configuration['custom_cell_alignment'][col_idx]

                tbl += ">"
                tbl += col

                if row_idx < len(rows) and col_idx < len(columns) - 1:
                    tbl += "</TD>"

            if row_idx < len(rows) - 1:
                tbl += "</TD></TR>\n"

        tbl += "\n"
        tbl += "</TD></TR>"
        tbl += "</TABLE></DIV>\n"
        return tbl

    def create_table_with_columns_based_on_newlines(self, paragraph, separator):
        rows = []
        lines = paragraph.splitlines()
        for line in lines:
            rows.append(line.split(separator))
        return rows

    def create_table_with_fixed_number_of_columns(self, paragraph, separator, num_columns):
        cells = paragraph.split(separator)
        current_row = []
        rows = []

        for cell in cells:
            current_row.append(cell.strip('\n'))

            if len(current_row) == num_columns:
                rows.append(current_row)
                current_row = []

        if len(current_row) > 0:
            rows.append(current_row)

        return rows

class Txt2Html(object):
    def __init__(self):
        self.markup = Markup()
        self.format = Formatting(self.markup)
        self.append_page_break = False
        self.create_title = False
        self.page_title = ""

    def convert(self, content):
        converted = "<HTML>\n"

        if len(content) > 0:
            self.parse_link_aliases_and_find_title(content)

            if self.create_title and self.page_title != "":
                converted += "<HEAD>\n"
                converted += "<TITLE>%s</TITLE>\n" % self.page_title
                converted += "</HEAD>\n"

            converted += self.transform_paragraphs(content)

        if self.append_page_break:
            converted += "<!-- PAGE BREAK -->\n"

        converted += "</HTML>\n"
        return converted

    def parse_link_aliases_and_find_title(self, content):
        for paragraph in self.paragraphs(content):
            self.convert_paragraph(paragraph)
        self.page_title = self.format.first_header

    def transform_paragraphs(self, content):
        converted = ""
        for paragraph in self.paragraphs(content):
            converted += self.convert_paragraph(paragraph)
        return converted

    def convert_paragraph(self, paragraph):
        if self.is_raw_html_paragraph(paragraph):
            return paragraph + '\n'

        if self.has_formatting(paragraph):
            paragraph = self.do_markup(paragraph)
            return self.do_formatting(paragraph)

        return self.format.paragraph(self.do_markup(paragraph)) + "\n"

    def has_formatting(self, paragraph):
        return self.last_word(paragraph).startswith(":")

    def last_word(self, text):
        return text.split()[-1]

    def do_formatting(self, paragraph):
        last_word = self.last_word(paragraph)
        format_str = paragraph[paragraph.rfind(last_word):]
        format_str = format_str.strip('\n')
        paragraph = paragraph.replace(format_str, "")
        commands = format_str[1:].strip()
        command_regex = r"(?P<command>[^\(,]+(\([^\)]+\))?),?"
        command_pattern = re.compile(command_regex)

        for command, _ in reversed(command_pattern.findall(commands)):
            paragraph = self.format.convert(command, paragraph)

        return paragraph + '\n'

    def do_markup(self, paragraph):
        return self.markup.convert(paragraph)

    def paragraphs(self, content):
        paragraph = []
        last_line_had_format = False

        for line in self.lines(content):
            if self.is_paragraph_separator(line) or last_line_had_format:
                if len(paragraph) > 0:
                    yield '\n'.join(paragraph) + '\n'

                if self.is_paragraph_separator(line):
                    paragraph = []
                    last_line_had_format = False
                else:
                    paragraph = [line]
                    last_line_had_format = self.has_formatting(line)
            else:
                paragraph.append(line)
                last_line_had_format = self.has_formatting(line)

        if len(paragraph) > 0:
            yield '\n'.join(paragraph) + '\n'

    def is_raw_html_paragraph(self, paragraph):
        return paragraph.startswith('<') and paragraph.endswith('>\n')

    def is_paragraph_separator(self, line):
        return len(line) == 0 or line.isspace()

    def lines(self, content):
        lines = content.splitlines()
        current_line = ""
        i = 0

        while i < len(lines):
            current_line += lines[i]

            if current_line.endswith("\\"):
                current_line = current_line[0:-1]
            else:
                yield current_line
                current_line = ""

            i += 1

def get_argument_parser():
    parser = argparse.ArgumentParser(description='converts a text file with simple formatting & markup into HTML.\n'
                                                 'formatting & markup specification is given in README')
    parser.add_argument('-b', dest='breakflag', action='store_true', help='add a page-break comment to end of each HTML'
                                                                          ' file. useful when set of HTML files will be'
                                                                          ' converted to PDF')
    parser.add_argument('-x', metavar='file-to-skip', dest='skip_files', action='append')
    parser.add_argument('--generate-title', dest='create_title', action='store_true', help='add HTML head page title '
                                                                                           'based on first h1,h2,h3,'
                                                                                           'h4... element')
    parser.add_argument('files',  metavar='file', nargs='+', help='one or more files to convert')
    return parser

def get_output_filename(path):
    filename, ext = os.path.splitext(path)
    return filename + ".html"

def main(args=sys.argv[1:], out=sys.stdout, err=sys.stderr):
    parser = get_argument_parser()
    parsed_args = parser.parse_args(args)

    write_to_files = len(parsed_args.files) > 1

    for filename in parsed_args.files:
        if parsed_args.skip_files and filename in parsed_args.skip_files:
            continue

        with open(filename, 'r') as f:
            print("Converting", filename, "...", file=err)
            content = f.read()
            converter = Txt2Html()
            converter.append_page_break = parsed_args.breakflag
            converter.create_title = parsed_args.create_title

            result = converter.convert(content)

            if write_to_files:
                output_filename = get_output_filename(filename)
                with open(output_filename, "w+t") as outfile:
                    outfile.write(result)
            else:
                print(result, end='', file=out)

if __name__ == "__main__":
    main()
