import sublime
import sublime_plugin
import re
import time
import os

SETTINGS = {}
lastCompletion = {"needFix": False, "value": None, "region": None}

def plugin_loaded():
    get_settings()

def get_settings():
    settings = sublime.load_settings('cssrem.sublime-settings')
    SETTINGS['px_to_rem'] = settings.get('px_to_rem', 40)
    SETTINGS['max_rem_fraction_length'] = settings.get('max_rem_fraction_length', 6)
    SETTINGS['available_file_types'] = settings.get('available_file_types', ['.css', '.less', '.sass'])

def get_setting(view, key):
    return view.settings().get(key, SETTINGS[key]);

class CssRemCommand(sublime_plugin.EventListener):
    def on_text_command(self, view, name, args):
        if name == 'commit_completion':
            view.run_command('replace_rem')
            # pass
        return None

    def on_query_completions(self, view, prefix, locations):
        print('cssrem start {0}, {1}'.format(prefix, locations))

        # only works on specific file types
        fileName, fileExtension = os.path.splitext(view.file_name())
        if not fileExtension.lower() in SETTINGS['available_file_types']:
            return []

        # reset completion match
        lastCompletion["needFix"] = False
        location = locations[0]
        snippets = []

        # get rem match
        match = checkRemMatched(prefix)
        if match:
            lineLocation = view.line(location)
            line = view.substr(sublime.Region(lineLocation.a, location))
            value = match.group(1)
            
            # fix: values like `0.5px`
            segmentStart = line.rfind(" ", 0, location)
            if segmentStart == -1:
                segmentStart = 0
            segmentStr = line[segmentStart:location]

            segment = re.compile("([\d.])+" + value).search(segmentStr)
            if segment:
                value = segment.group(0)
                start = lineLocation.a + segmentStart + 0 + segment.start(0)
                lastCompletion["needFix"] = True
            else:
                start = location

            remValue = round(float(value) / SETTINGS['px_to_rem'], SETTINGS['max_rem_fraction_length'])

            # save them for replace fix
            lastCompletion["value"] = str(remValue) + 'rem'
            lastCompletion["region"] = sublime.Region(start, location)

            # set completion snippet
            snippets += [(value + 'px ->rem(' + str(SETTINGS['px_to_rem']) + ')', str(remValue) + 'rem')]

        # print("cssrem: {0}".format(snippets))
        return snippets

def checkRemMatch(prefix):
    regexp = re.compile("([\d.]+)p(x)?")
    match = regexp.match(prefix)
    return match

class ReplaceRemCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        needFix = lastCompletion["needFix"]
        if needFix == True:
            value = lastCompletion["value"]
            region = lastCompletion["region"]
            # print('replace: {0}, {1}'.format(value, region))
            self.view.replace(edit, region, value)
            self.view.end_edit(edit)