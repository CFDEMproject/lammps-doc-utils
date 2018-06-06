# LIGGGHTS Documentation Utilities
#
# Copyright (C) 2016 Andreas Aigner
#
# Based on the work from Richard Berger.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

def detect_local_toc(paragraph):
    local_toc_pattern = re.compile(r"[0-9]+\.[0-9]*\s+.+<BR>", re.MULTILINE)

    m = local_toc_pattern.match(paragraph)

    if m:
        return ""

    return paragraph

def indent(content):
    indented = ""
    for line in content.splitlines():
        indented += "   %s\n" % line
    return indented

def detect_and_format_notes(paragraph):
    note_pattern = re.compile(r"(?P<type>(IMPORTANT )?NOTE):\s+(?P<content>.+)", re.MULTILINE | re.DOTALL)

    if note_pattern.match(paragraph):
        m = note_pattern.match(paragraph)
        content = m.group('content')
        content = indent(content.strip())

        if m.group('type') == 'IMPORTANT NOTE':
            paragraph = '.. warning::\n\n' + content + '\n'
        else:
            paragraph = '.. note::\n\n' + content + '\n'
    return paragraph

def detect_and_add_command_to_index(content):
    command_pattern = re.compile(r"(?:.+`)?(?P<command>[\w/\s]+)(?:<.+>`)?\s+command\s+\=+\s+")
    m = command_pattern.findall(content)

    model_pattern = re.compile(r"(?:.+`)?(?P<model>[\w/\s]+)(?:<.+>`)?\s+model\s+\=+\s+")
    n = model_pattern.findall(content)

    mesh_module_pattern = re.compile(r"(?P<module>^mesh module[\w/\s]+)(?:<.+>`)?\s+\=+\s+")
    o = mesh_module_pattern.findall(content)

    if m:
        index = ".. index:: %s\n\n" % ', '.join(m)
        return index + content

    # if no command, there may be a model
    if n:
        index = ".. index:: %s\n\n" % ', '.join(n)
        return index + content

    # ... or a mesh module
    if o:
        index = ".. index:: %s\n\n" % ', '.join(o)
        return index + content

    return content

def filter_file_header_until_first_horizontal_line(content):
    hr = '----------\n\n'
    first_hr = content.find(hr)

    common_links = "\n.. _liws: http://www.cfdem.com\n" \
                   ".. _ld: Manual.html\n" \
                   ".. _lc: Section_commands.html#comm\n"

    if first_hr >= 0:
        return content[first_hr+len(hr):].lstrip() + common_links
    return content

def promote_doc_keywords(content):
    content = content.replace('**Syntax:**\n', 'Syntax\n'
                                               '""""""\n')
    content = content.replace('**Examples:**\n', 'Examples\n'
                                                 '""""""""\n')
    content = content.replace('**LIGGGHTS(R) vs. LAMMPS info:**\n', 'LIGGGHTS(R) vs. LAMMPS info\n'
                                                                   '"""""""""""""""""""""""""""\n')
    content = content.replace('**Description:**\n', 'Description\n'
                                                    '"""""""""""\n')
    content = content.replace('**Restart, fix_modify, output, run start/stop, minimize info:**\n',
                              'Restart, fix_modify, output, run start/stop, minimize info\n'
                              '""""""""""""""""""""""""""""""""""""""""""""""""""""""""""\n')
    content = content.replace('**Restart, fix_modify, run start/stop, minimize info:**\n',
                              'Restart, fix_modify, run start/stop, minimize info\n'
                              '""""""""""""""""""""""""""""""""""""""""""""""""""\n')
    content = content.replace('**Output info:**\n', 'Output info\n'
                                                    '"""""""""""\n')
    content = content.replace('**Restrictions:**', 'Restrictions\n'
                                                   '""""""""""""\n')
    content = content.replace('**Related commands:**\n', 'Related commands\n'
                                                         '""""""""""""""""\n')
    content = content.replace('**Default:**\n', 'Default\n'
                                                '"""""""\n')
    return content

def filter_multiple_horizontal_rules(content):
    return re.sub(r"----------[\s\n]+----------", '', content)
