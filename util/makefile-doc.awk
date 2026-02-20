#!/usr/bin/awk -f
# Generate docs for Makefile variables and targets
#
#    File: makefile-doc.awk
#  Author: Dimitar Dimitrov
# License: Apache-2.0
# Project: https://github.com/drdv/makefile-doc
# Version: v1.4
#
# Usage (see project README.md for more details):
#   awk [-v option=value] -f makefile-doc.awk [Makefile ...]
#
# Notes:
#   * In the code, the term anchor is used to refer to Makefile targets / variables.
#   * Docs can be placed above an anchor or inline (the latter is discarded if the
#     former is present).
#   * Anchor docs can start with the following tokens:
#      * ##  default anchors (displayed in COLOR_DEFAULT)
#      * ##! special anchors (displayed in COLOR_ATTENTION)
#      * ##% deprecated anchor (displayed in COLOR_DEPRECATED)
#   * The token ##@ can be used to create sections (displayed in COLOR_SECTION)
#
# Options (possible values are given in {...}, (.) denotes the default):
#   + OUTPUT_FORMAT: {(ANSI), HTML, LATEX}
#   + EXPORT_THEME: see below
#   + SUB: see below
#   + TARGETS_REGEX: regex for matching targets
#   + VARIABLES_REGEX: regex for matching variables
#   * VARS: {0, (1)} show documented variables
#   * PADDING: {(" "), ".", ...} a single padding character between anchors and docs
#   * DEPRECATED: {0, (1)} show deprecated anchors
#   * OFFSET: {0, 1, (2), ...} number of spaces to offset docs from anchors
#   + RECIPEPREFIX: should have the same value as the .RECIPEPREFIX from your Makefile
#   * see as well the color codes below
#
# Color codes (https://en.wikipedia.org/wiki/ANSI_escape_code):
#   * COLOR_DEFAULT: (34) blue
#   * COLOR_ATTENTION: (31) red
#   * COLOR_DEPRECATED: (33) yellow
#   * COLOR_SECTION: (32) green
#   * COLOR_WARNING: (35) magenta -- currently not used
#   * COLOR_BACKTICKS: (0) disabled -- used for text in backticks in docs
#
#   Colors are specified using the parameter in ANSI escape codes, e.g., the parameter
#   for blue is the 34 in `\033[34m`. The supported parameters are: 0, 1, 3, 4, 9,
#   30-37, 40-47, 90-97, 100-107 (see array ANSI_TO_HTML_COLOR).
#
#   + EXPORT_THEME: user-defined mapping between ANSI color parameters and HEX color
#     codes (without the hash tag). For example -v EXPORT_THEME=32:d33682,35:859900
#     would change the way the ANSI colors corresponding to the parameters 32 and 35 are
#     exported to HTML and LATEX (in effect, exchanging their default values in this
#     example). This can be used to define a custom theme for HTML and LATEX output (it
#     has no effect on ANSI output).
#
# SUB:
#   Contains substitutions for targets and variables. For example, consider a variable
#   named AWK whose possible values are contained in a variable SUPPORTED_AWK_VARIANTS,
#   then passing -v SUB='AWK:$(SUPPORTED_AWK_VARIANTS)' would add the values of
#   SUPPORTED_AWK_VARIANTS to the documentation of the variable AWK. This mechanism is
#   also useful when documenting targets defined in terms of variables/expressions,
#   which we might want to rename. The format of a single substitution is
#   [<p1:v1,...>]NAME[:LABEL]:[VALUES]
#   + NAME is the name of the variable/target to substitute in the documentation
#   + LABEL is an optional label for renaming the variable/target
#   + VALUES are optional space-separated values to include (a comma can appear as a
#     part of a value if it is escaped, i.e., \\,)
#   + <p1:v1,...> are optional, comma-separated, key-value pairs with parameters
#   + multiple ;-separated substitutions can be passed
#
# SUB parameters:
#   Each substitution can include parameters <p1:v1,...>:
#   + L:0/L:1 values are displayed starting from the current/next line
#   + M:0/M:1 single/multi-line display
#   + N       max number of values to display (-1, the default, means no limit)
#   + S       value-separator
#   + P       prefix (added to each value)
#   + I       initial string, e.g., {
#   + T       termination string, e.g., }
#
# Code conventions:
#   * All local variables in functions should be defined in the function signature (awk
#     is a bit special in that respect).
#   + The naming convention for global variables is:
#     + long-standing/important global variables are written in all upper case
#     + temporary variables that end-up being global (simply because of where they are
#       defined, e.g., in the END stanza) have a prefix g_.
#   * The code is meant to run with most major awk implementations, and as a result we
#     need to stick to basic syntax. For example, we cannot use a match function with
#     a third argument (an array that stores the groups) and have to fall-back to using
#     RSTART and RLENGTH. We cannot use arrays of arrays (as in gnu awk). We cannot use
#     %* patterns, some regex features etc.
#   + Notes on the arrays in the code:
#     Order is important only to the arrays DESCRIPTION_DATA, SECTION_DATA, TARGETS,
#     VARIABLES and each of them has an associated *_INDEX integer variable.
#
# Terminology and definitions:
#   + A Makefile rule (without patterns) can take one of the following forms:
#     target-name [...] [&]:[:] [prerequisits] [;] [inline recipe]
#         [recipe]
#
#     target-name [...] [&]:[:] [variable assignment]
#         [recipe]
#
#     where:
#       variable assignment: a single variable can be assigned per rule
#       prerequisits := normal-prerequisites | order-only-prerequisites
#       inline recipe := [command] [; command ...]
#       recipe := [command]
#                 [...]
#
#     with normal-prerequisites and order-only-prerequisites being space separated lists
#     of target names.
#   + Recipe: a sequence of commands executed in the shell. A recipe (and thus a rule)
#     ends at the next target line, variable assignment, define ... endef
#   + Target: an abstraction representing a task/goal to achieve which is defined in
#     terms of, potentially, many rules.
#     + Normal (single-colon) targets can have only one recipe and to mirror this we
#       allow for them to have only one description.
#     + double-colon targets (i.e., targets defined by double-colon rules) can have
#       multiple descriptions (as they can have multiple recipes).
#   + Target line: the top-line (the header) of a Makefile rule
#   + Target name: a (string) label for a target
#   + Description of a rule: comments starting with ##, ##! or ##% placed above the
#     target line of a rule or inline. Inline descriptions placed after an inline recipe
#     are ignored.
#   + The last rule with a description defines the description of a normal target, while
#     every double-colon rule with a description defines a new description.

function max(x, y) {
  return (x >= y) ? x : y
}

function min(x, y) {
  return (x <= y) ? x : y
}

function repeated_string(string, n, #locals
                         s) {
  s = sprintf("%" n "s", "")
  if (string) {
    gsub(/ /, string, s)
  }
  return s
}

# in POSIX-compliant AWK the length function works on strings but not on arrays
function length_array_posix(array, #locals
                            key, n) {
  n = 0
  for (key in array) {
    n++
  }
  return n
}

function form_dc_target_name(target_name_nominal) {
  if (!(target_name_nominal in TARGETS_DC_COUNTER)) {
    TARGETS_DC_COUNTER[target_name_nominal] = 1
  }

  return sprintf("%s%s%s",
                 target_name_nominal,
                 DOUBLE_COLON_SEPARATOR,
                 TARGETS_DC_COUNTER[target_name_nominal])
}

# assumes that array is produced from split()
function join_splitted(array, delimiter, #locals
                       string, k, n) {
  string = ""
  n = length_array_posix(array)
  for (k=1; k<=n; k++) {
    if (k == 1) {
      string = array[k]
    } else {
      string = string delimiter array[k]
    }
  }
  return string
}

function strip_start_end_spaces_tabs(string) {
  sub(/^[ \t]*/, "", string)
  sub(/[ \t]*$/, "", string)
  return string
}

# we have to escape {...} in \begin{alltt} ... \end{alltt}
function escape_braces_for_latex_output(text) {
  if (OUTPUT_FORMAT == "LATEX") {
    gsub(/\{/, "\\{", text)
    gsub(/\}/, "\\}", text)
  }
  return text
}

function get_tag_from_description(string, #locals
                                  tag) {
  if (match(string, /^ *(##!|##%|##)/)) {
    tag = substr(string, RSTART, RLENGTH)
    sub(/ */, "", tag)
    return tag
  }

  return 0 # if we end-up here it probably means that we are using a wrong regex
}

function save_description_data(string) {
  DESCRIPTION_DATA[DESCRIPTION_DATA_INDEX++] = string
}

function forget_descriptions_data() {
  delete DESCRIPTION_DATA
  DESCRIPTION_DATA_INDEX = 1
}

function parse_inline_descriptions(whole_line, #locals
                                   inline_description, part_before_description) {
  if (!(match(whole_line, /^[^#]*;/)) &&
      match(whole_line, / *(##!|##%|##)/)) {
    inline_description = substr(whole_line, RSTART)
    sub(/^ */, "", inline_description)
    save_description_data(inline_description)
  }
}

function detect_ignored_targets(target_line, #locals
                                key) {
  sub(/^[ \t]*/, "", target_line)
  for (key in IGNORED_TARGETS) {
    if (target_line ~ "^" IGNORED_TARGETS[key] " *:") {
      return 1
    }
  }
  return 0
}

function initialize_variables_regex() {
  ASSIGNMENT_OPERATORS_PATTERN = "(=|:=|::=|:::=|!=|\\?=|\\+=)"
  split("override unexport export private", VARIABLE_QUALIFIERS, " ")
  VARIABLES_REGEX_DEFAULT = sprintf("^ *( *(%s) *)* *[^#][a-zA-Z0-9_-]* *%s",
                                    join_splitted(VARIABLE_QUALIFIERS, "|"),
                                    ASSIGNMENT_OPERATORS_PATTERN)
}

function parse_variable_name(whole_line, #locals
                             whole_line_split, variable_name, k) {
  split(whole_line, whole_line_split, ASSIGNMENT_OPERATORS_PATTERN)
  variable_name = whole_line_split[1]

  # here we need to preserve order in order to remove unexport and not just export
  for (k=1;
       k<=length_array_posix(VARIABLE_QUALIFIERS);
       k++) {
    gsub("(^| )" VARIABLE_QUALIFIERS[k] "( |$)", " ", variable_name)
  }
  strip_start_end_spaces_tabs(variable_name)
  return variable_name
}

function associate_data_with_anchor(anchor_name,
                                    anchors,
                                    anchors_index,
                                    anchors_description_data,
                                    anchors_section_data,
                                    anchor_type) {
  if (anchor_name in anchors_description_data) {
    if (!(anchor_type == "variable" && !VARS)) {
      printf("WARNING: [%s:%s] redefined docs of %s: %s\n",
             FILENAME,
             FNR,
             anchor_type,
             anchor_name) > STDERR
    }
  } else {
    anchors[anchors_index] = anchor_name
    anchors_index++
  }

  anchors_description_data[anchor_name] = assemble_description_section_data(DESCRIPTION_DATA)
  forget_descriptions_data()

  # note that section data is associated only with documented anchors
  if (length_array_posix(SECTION_DATA) > 0) {
    if (anchor_name in anchors_section_data) {
      printf("WARNING: [%s:%s] redefined associated section data: %s\n",
             FILENAME,
             FNR,
             anchor_name) > STDERR
    }

    anchors_section_data[anchor_name] = assemble_description_section_data(SECTION_DATA)
    forget_section_data()
  }

  return anchors_index
}

function save_section_data(string) {
  SECTION_DATA[SECTION_DATA_INDEX++] = string
}

function forget_section_data() {
  delete SECTION_DATA
  SECTION_DATA_INDEX = 1
}

function get_associated_section_data(anchor_name,
                                     anchor_section_data) {
  if (anchor_name in anchor_section_data) {
    return colorize_description_backticks(\
        apply_output_specific_formatting(anchor_section_data[anchor_name]))
  }
  return 0 # means that there is no section data associated with this anchor
}

function get_max_anchor_length(anchors, #locals
                               max_len, key, anchor, n) {
  max_len = 0
  for (key in anchors) { # order is not important
    anchor = anchors[key]
    n = (anchor in SUB_LABELS) ? length(SUB_LABELS[anchor]) : length(anchor)
    if (n > max_len) {
      max_len = n
    }
  }
  return max_len
}

function get_separator(character, len_anchors) {
  return repeated_string(character, max(len_anchors,
                                        max(length(HEADER_TARGETS),
                                            length(HEADER_VARIABLES))))
}

function substitute_backticks_patterns(string, #locals
                                       before_match, inside_match, after_match) {
  # --------------------------------------------------------------------------
  # Since I cannot use this code in mawk and nawk, I implemented a manual hack
  # --------------------------------------------------------------------------
  # replace_with = COLOR_BACKTICKS_CODE "\\1" COLOR_RESET_CODE
  # return gensub(/`([^`]+)`/, replace_with, "g", description) # only for gawk
  # --------------------------------------------------------------------------
  while (match(string, /`([^`]+)`/)) {
    before_match = substr(string, 1, RSTART - 1)
    inside_match = substr(string, RSTART + 1, RLENGTH - 2)
    after_match = substr(string, RSTART + RLENGTH)

    string = sprintf(repeated_string("%s", 5),
                     before_match,
                     COLOR_BACKTICKS_CODE,
                     inside_match,
                     COLOR_RESET_CODE,
                     after_match)
  }
  return string
}

function colorize_description_backticks(description) {
  if (COLOR_BACKTICKS) {
    return substitute_backticks_patterns(description)
  }
  return description
}

# The input contains the (\n separated) description lines associated with one anchor.
# Each line starts with a tag (##, ##! or ##%). Here we have to strip them and to
# introduce indentation for lines below the first one.
function format_description_data(anchor_name,
                                 anchors_description_data,
                                 len_anchor_names,
                                 #locals
                                 k, array_of_lines, line, description) {
  # the automatically-assigned indexes during the split are: 1, ..., #lines
  split(anchors_description_data[anchor_name], array_of_lines, "\n")

  # the tag for the first line is stripped below (after the parameter update)
  description = repeated_string("", OFFSET) array_of_lines[1]

  for (k=2;
       k<=length_array_posix(array_of_lines);
       k++) {
    line = array_of_lines[k]
    sub(/^(##|##!|##%)/, "", line) # strip the tag
    description = sprintf("%s\n%s%s",
                          description,
                          repeated_string("", OFFSET + len_anchor_names),
                          line)
  }

  update_display_parameters(description)
  # The order of alternatives is important when using goawk v1.29.1 and below.
  # Starting from goawk v1.30.0 this problem has been fixed.
  sub(/(##!|##%|##)/, "", description) # strip the tag (keep the leading space)
  return colorize_description_backticks(apply_output_specific_formatting(description))
}

function assemble_description_section_data(array, #locals
                                           docs, k) {
  docs = array[1]
  for (k=2; k<=length_array_posix(array); k++) {
    docs = docs "\n" array[k]
  }
  return docs
}

function update_display_parameters(description, #locals
                                   tag) {
  tag = get_tag_from_description(description)
  if (tag == "##!") {
    DISPLAY_PARAMS["color"] = COLOR_ATTENTION_CODE
    DISPLAY_PARAMS["show"] = 1
  } else if (tag == "##%") {
    DISPLAY_PARAMS["color"] = COLOR_DEPRECATED_CODE
    DISPLAY_PARAMS["show"] = DEPRECATED
  } else if (tag == "##") {
    DISPLAY_PARAMS["color"] = COLOR_DEFAULT_CODE
    DISPLAY_PARAMS["show"] = 1
  } else {
    printf("ERROR (we shouldn't be here): %s\n", description) > STDERR
    exit 1
  }
}

function extract_substitution_params(string_with_parameters, #locals
                                     temp_placeholder, k, key_values, pair, key) {
  delete SUB_PARAMS_CURRENT
  temp_placeholder = "\034" # the “file separator” ASCII control character

  # temporarily replace escaped commas
  gsub(/\\,/, temp_placeholder, string_with_parameters)
  for (k=1;
       k<=split(string_with_parameters, key_values, ",");
       k++) {
    gsub(temp_placeholder, ",", key_values[k]) # restore commas
    split(key_values[k], pair, ":")
    gsub(SPACES_TABS_REGEX, "", pair[1])
    SUB_PARAMS_CURRENT[pair[1]] = pair[2]
  }

  for (key in SUB_PARAMS_DEFAULTS) {
    if (!(key in SUB_PARAMS_CURRENT)) {
      SUB_PARAMS_CURRENT[key] = SUB_PARAMS_DEFAULTS[key]
    }
  }
}

function form_substitutions(                                            \
    split_substitutions, k, string, substitution_params, substitution_rest,
    key_value_parts) {
  for (k=1;
       k<=split(SUB, split_substitutions, ";");
       k++) {
    string = split_substitutions[k]

    # Extract optional params in a <...> prefix
    if (match(string, /^<([^>]*)>/)) {
      substitution_params = substr(string, RSTART+1, RLENGTH-2) # strip < and >
      substitution_rest = substr(string, RSTART + RLENGTH)
    } else {
      substitution_params = ""
      substitution_rest = string
    }

    split(substitution_rest, key_value_parts, ":")
    gsub(SPACES_TABS_REGEX, "", key_value_parts[1])

    SUB_PARAMS[key_value_parts[1]] = substitution_params
    if (length_array_posix(key_value_parts) == 1) {
      printf("WARNING: a minimal substitution is -v SUB='NAME:'\n") > STDERR
    }
    else if (length_array_posix(key_value_parts) == 2) {
      SUB_VALUES[key_value_parts[1]] = key_value_parts[2]
    } else {
      SUB_VALUES[key_value_parts[1]] = key_value_parts[3]
      SUB_LABELS[key_value_parts[1]] = key_value_parts[2]
    }
  }
}

function initialize_substitution_parameter_defaults() {
  # don't change the defaults
  SUB_PARAMS_DEFAULTS["L"] = 1 # 0: start display on current line, 1: start display on next line
  SUB_PARAMS_DEFAULTS["M"] = 1 # 1: multi-line display, 0: single-line display
  SUB_PARAMS_DEFAULTS["N"] = -1 # max number of elements to display (-1 means no limit)
  SUB_PARAMS_DEFAULTS["S"] = "" # separator
  SUB_PARAMS_DEFAULTS["P"] = "" # prefix
  SUB_PARAMS_DEFAULTS["I"] = "" # initial string, e.g., (
  SUB_PARAMS_DEFAULTS["T"] = "" # termination string, e.g., , ...)
}

function display_substitutions(anchor, len_anchors, #locals
                               k, n, L, M, I, value_parts, offset,
                               cond_indent, indentation, text) {
  split(SUB_VALUES[anchor], value_parts, " ")

  if (SUB_PARAMS_CURRENT["N"] < 0) {
    n = length_array_posix(value_parts)
  } else {
    n = min(SUB_PARAMS_CURRENT["N"], length_array_posix(value_parts))
  }

  for (k=1; k<=n; k++) {
    L = SUB_PARAMS_CURRENT["L"]
    M = SUB_PARAMS_CURRENT["M"]
    I = SUB_PARAMS_CURRENT["I"]

    # -----------------------------
    # NO INDENT: !M && !L
    #    INDENT: !M &&  L && k == 1
    # NO INDENT: !M &&  L && k  > 1
    # NO INDENT:  M && !L && k == 1
    #    INDENT:  M && !L && k  > 1
    #    INDENT:  M &&  L
    # -----------------------------
    # the + 1 is because of the usual one space we add between the token ## and the docs
    indentation = len_anchors + OFFSET + 1  + (M && k > 1 ? length(I) : 0)
    cond_indent = (!M && L && k == 1) || (M && !L && k > 1) || (M && L)
    text = sprintf(repeated_string("%s", 7),
                   repeated_string("", cond_indent ? indentation : 1),
                   k == 1 ? I : "",
                   SUB_PARAMS_CURRENT["P"],
                   value_parts[k],
                   k == n ? "" : SUB_PARAMS_CURRENT["S"],
                   k == n ? SUB_PARAMS_CURRENT["T"] : "",
                   M || (!M && k == n) ? "\n" : "")
    printf(colorize_description_backticks(apply_output_specific_formatting(text)))
  }
}

function display_anchor_with_data(anchor, description, section, len_anchors, #locals
                                  renamed_anchor, formatted_anchor, padding,
                                  normalized_anchor_name) {
  extract_substitution_params(SUB_PARAMS[anchor])

  # Display the section (if there is one) even if it is anchored to a deprecated anchor
  # that is not to be displayed.
  if (section) {
    if (COLOR_SECTION_CODE) {
      printf("%s%s%s\n", COLOR_SECTION_CODE, section, COLOR_RESET_CODE)
    } else {
      printf("%s\n", section)
    }
  }

  if (DISPLAY_PARAMS["show"]) {
    renamed_anchor = (anchor in SUB_LABELS) ? SUB_LABELS[anchor] : anchor
    formatted_anchor = apply_output_specific_formatting(renamed_anchor)

    # handle padding manually because there is a difference between the actual text and
    # the visible text (for latex)
    padding = repeated_string("", len_anchors - length(renamed_anchor))
    if (DISPLAY_PARAMS["color"]) {
      formatted_anchor = sprintf("%s%s%s%s",
                                 DISPLAY_PARAMS["color"],
                                 formatted_anchor,
                                 padding,
                                 COLOR_RESET_CODE)
    } else {
      formatted_anchor = sprintf("%s%s", formatted_anchor, padding)
    }

    if (PADDING != " ") {
      gsub(/ /, PADDING, formatted_anchor)
    }

    printf("%s%s%s",
           formatted_anchor,
           description,
           SUB_PARAMS_CURRENT["L"] ? "\n" : "")
  }
  display_substitutions(anchor, len_anchors)
}

# formatting functions to be applied just before colors have been added
function apply_output_specific_formatting(text) {
  return escape_braces_for_latex_output(text)
}

# the user can change separately colors in the ranges 30-37 and 40-47
function set_user_defined_color_theme(                                  \
    html_colors_split, key, ansi_html_map, ansi_param, html_color_code) {
  # format: ANSI_PARAM:HTML_COLOR_CODE[,...]
  if (EXPORT_THEME) {
    split(EXPORT_THEME, html_colors_split, ",")
    for (key in html_colors_split) {
      split(html_colors_split[key], ansi_html_map, ":")
      ansi_param = ansi_html_map[1]
      html_color_code = ansi_html_map[2]
      # values in the range 0-9 cannot be modified
      if (ansi_param > 9 && ansi_param in ANSI_TO_HTML_COLOR) {
        ANSI_TO_HTML_COLOR[ansi_param] = html_color_code
      }
    }
  }
}

# The solarized theme is used by default
# https://github.com/altercation/solarized?tab=readme-ov-file#the-values
function define_ansi_to_html_colors(            \
    k) {
  # no foreground/background by default
  ANSI_TO_HTML_COLOR["BG"] = -1 # "000000"
  ANSI_TO_HTML_COLOR["FG"] = -1 # "AAAAAA"

  ANSI_TO_HTML_COLOR[0] = ""
  ANSI_TO_HTML_COLOR[1] = "bold"
  ANSI_TO_HTML_COLOR[3] = "italic"
  ANSI_TO_HTML_COLOR[4] = "underline"
  ANSI_TO_HTML_COLOR[9] = "line-through"

  ANSI_TO_HTML_COLOR[30] = "073642" # black
  ANSI_TO_HTML_COLOR[31] = "dc322f" # red
  ANSI_TO_HTML_COLOR[32] = "859900" # green
  ANSI_TO_HTML_COLOR[33] = "b58900" # yellow
  ANSI_TO_HTML_COLOR[34] = "268bd2" # blue
  ANSI_TO_HTML_COLOR[35] = "d33682" # magenta
  ANSI_TO_HTML_COLOR[36] = "2aa198" # cyan
  ANSI_TO_HTML_COLOR[37] = "eee8d5" # white

  ANSI_TO_HTML_COLOR[90] = "002b36" # brblack
  ANSI_TO_HTML_COLOR[91] = "cb4b16" # brred
  ANSI_TO_HTML_COLOR[92] = "586e75" # brgreen
  ANSI_TO_HTML_COLOR[93] = "657b83" # bryellow
  ANSI_TO_HTML_COLOR[94] = "839496" # brblue
  ANSI_TO_HTML_COLOR[95] = "6c71c4" # brmagenta
  ANSI_TO_HTML_COLOR[96] = "93a1a1" # brcyan
  ANSI_TO_HTML_COLOR[97] = "fdf6e3" # brwhite

  for (k=30; k<=37; k++) { ANSI_TO_HTML_COLOR[k+10] = ANSI_TO_HTML_COLOR[k] }
  for (k=90; k<=97; k++) { ANSI_TO_HTML_COLOR[k+10] = ANSI_TO_HTML_COLOR[k] }

  set_user_defined_color_theme()
}

function define_ansi_to_html_attributes(        \
    k) {
  ANSI_TO_HTML_ATTR[0] = ""
  ANSI_TO_HTML_ATTR[1] = "font-weight"
  ANSI_TO_HTML_ATTR[3] = "font-style"
  ANSI_TO_HTML_ATTR[4] = "text-decoration"
  ANSI_TO_HTML_ATTR[9] = "text-decoration"

  for (k=30; k<=37; k++) { ANSI_TO_HTML_ATTR[k] = "color" }
  for (k=40; k<=47; k++) { ANSI_TO_HTML_ATTR[k] = "background-color" }
  for (k=90; k<=97; k++) { ANSI_TO_HTML_ATTR[k] = "color" }
  for (k=100; k<=107; k++) { ANSI_TO_HTML_ATTR[k] = "background-color" }
}

function define_ansi_to_latex_function(         \
    k) {
  ANSI_TO_LATEX_FUN[0] = ""
  ANSI_TO_LATEX_FUN[1] = "\\textbf"
  ANSI_TO_LATEX_FUN[3] = "\\emph"
  ANSI_TO_LATEX_FUN[4] = "\\uline"
  ANSI_TO_LATEX_FUN[9] = "\\sout"

  for (k=30; k<=37; k++) { ANSI_TO_LATEX_FUN[k] = "\\textcolor" }
  for (k=40; k<=47; k++) { ANSI_TO_LATEX_FUN[k] = "\\bgcolor" }
  for (k=90; k<=97; k++) { ANSI_TO_LATEX_FUN[k] = "\\textcolor" }
  for (k=100; k<=107; k++) { ANSI_TO_LATEX_FUN[k] = "\\bgcolor" }
}

function define_color_labels() {
  COLOR_LABELS["DEFAULT"] = "color-default"
  COLOR_LABELS["ATTENTION"] = "color-attention"
  COLOR_LABELS["DEPRECATED"] = "color-deprecated"
  COLOR_LABELS["SECTION"] = "color-section"
  COLOR_LABELS["WARNING"] = "color-warning"
  COLOR_LABELS["BACKTICKS"] = "color-backticks"
  COLOR_LABELS["FG"] = "makefile-doc-fg"
  COLOR_LABELS["BG"] = "makefile-doc-bg"
}

# here ansi_color_param is the normal ANSI color params, e.g., 30-37, but it could as
# well be "FG" or "BG"
function ansi_color_param_to_html_style(ansi_color_param, label, #locals
                                        template, attr) {
  if (ansi_color_param == "FG" || ansi_color_param == "BG") {
    if (ANSI_TO_HTML_COLOR[ansi_color_param] == -1) {
      return "" # indicates to not set any style
    }
    return sprintf("    .%s { %s: #%s; }\n",
                   COLOR_LABELS[label],
                   ansi_color_param == "FG" ? "color" : "background-color",
                   ANSI_TO_HTML_COLOR[ansi_color_param])
  }

  template = "    .%s %s\n"
  if (ansi_color_param && ansi_color_param in ANSI_TO_HTML_COLOR) {
    attr = ANSI_TO_HTML_ATTR[ansi_color_param]
    return sprintf(template,
                   COLOR_LABELS[label],
                   sprintf("{ %s: %s%s; }",
                           attr,
                           (attr == "color" || attr == "background-color")? "#" : "",
                           ANSI_TO_HTML_COLOR[ansi_color_param]))
  }

  return sprintf(template, COLOR_LABELS[label], "{}")
}

function ansi_color_param_to_latex_color(ansi_color_param, is_fgbg_definition) {
  if (ansi_color_param == "FG" || ansi_color_param == "BG") {
    if (ANSI_TO_HTML_COLOR[ansi_color_param] == -1) {
      return "" # indicates to not set any style
    }
    if (is_fgbg_definition) {
      return sprintf("\\definecolor{%s}{HTML}{%s}\n",
                     COLOR_LABELS[ansi_color_param],
                     ANSI_TO_HTML_COLOR[ansi_color_param])
    } else {
      if (ansi_color_param == "FG") {
        return sprintf("\\color{%s}\n", COLOR_LABELS["FG"])
      } else if (ansi_color_param == "BG") {
        return sprintf("\\pagecolor{%s}\n", COLOR_LABELS["BG"])
      }
    }
  }

  if (ansi_color_param &&
      ansi_color_param in ANSI_TO_HTML_COLOR &&
      ansi_color_param > 9) {
    return ANSI_TO_HTML_COLOR[ansi_color_param]
  }
  return "000000"
}

# ansi_color_param:
# == 0: no color
#  > 0: some color
#  < 0: reset token  (the user cannot set -1 from outside, see validate_ansi_param())
function define_color(ansi_color_param, color_label_key) {
  if (!ansi_color_param) {
    return "" # token for "no color annotation should be applied at all"
  }

  if (OUTPUT_FORMAT == "ANSI") {
    if (ansi_color_param == -1) {
      return "\033[0m"
    } else {
      return "\033[" ansi_color_param "m"
    }
  } else if (OUTPUT_FORMAT == "HTML") {
    if (ansi_color_param == -1) {
      return "</span>"
    } else {
      return "<span class=\"" COLOR_LABELS[color_label_key] "\">"
    }
  } else if (OUTPUT_FORMAT == "LATEX") {
    if (ansi_color_param == -1) {
      return "}"
    } else {
      if (ansi_color_param > 9) {
        return ANSI_TO_LATEX_FUN[ansi_color_param] "{" COLOR_LABELS[color_label_key] "}{"
      } else {
        return ANSI_TO_LATEX_FUN[ansi_color_param] "{"
      }
    }
  }
}

function validate_ansi_param(ansi_param) {
  if (ansi_param in ANSI_TO_HTML_COLOR) {
    # The explicit cast to int here is needed only because of a busybox awk bug
    # see misc/busybox_awk_bug_20251107.awk
    return int(ansi_param)
  }
  return 0
}

function initialize_colors() {
  define_ansi_to_html_colors()
  define_ansi_to_html_attributes()
  define_ansi_to_latex_function()
  define_color_labels()

  COLOR_DEFAULT = validate_ansi_param(COLOR_DEFAULT == "" ? 34 : COLOR_DEFAULT)
  COLOR_ATTENTION = validate_ansi_param(COLOR_ATTENTION == "" ? 31 : COLOR_ATTENTION)
  COLOR_DEPRECATED = validate_ansi_param(COLOR_DEPRECATED == "" ? 33 : COLOR_DEPRECATED)
  COLOR_WARNING = validate_ansi_param(COLOR_WARNING == "" ? 35 : COLOR_WARNING)
  COLOR_SECTION = validate_ansi_param(COLOR_SECTION == "" ? 32 : COLOR_SECTION)
  COLOR_BACKTICKS = validate_ansi_param(COLOR_BACKTICKS == "" ? 0 : COLOR_BACKTICKS)

  COLOR_DEFAULT_CODE = define_color(COLOR_DEFAULT, "DEFAULT")
  COLOR_ATTENTION_CODE = define_color(COLOR_ATTENTION, "ATTENTION")
  COLOR_DEPRECATED_CODE = define_color(COLOR_DEPRECATED, "DEPRECATED")
  COLOR_WARNING_CODE = define_color(COLOR_WARNING, "WARNING")
  COLOR_SECTION_CODE = define_color(COLOR_SECTION, "SECTION")
  COLOR_BACKTICKS_CODE = define_color(COLOR_BACKTICKS, "BACKTICKS")
  COLOR_RESET_CODE = define_color(-1)

  if (OUTPUT_FORMAT == "HTML") {
    HTML_FOOTER = "</pre>\n</div>"
    HTML_HEADER = sprintf("<head>\n  <style type=\"text/css\">\n%s%s%s%s%s%s%s%s  </style>\n</head>\n<div class=\"makefile-doc-fg makefile-doc-bg\">\n<pre>",
                          ansi_color_param_to_html_style(COLOR_ATTENTION, "ATTENTION"),
                          ansi_color_param_to_html_style(COLOR_SECTION, "SECTION"),
                          ansi_color_param_to_html_style(COLOR_DEPRECATED, "DEPRECATED"),
                          ansi_color_param_to_html_style(COLOR_DEFAULT, "DEFAULT"),
                          ansi_color_param_to_html_style(COLOR_WARNING, "WARNING"),
                          ansi_color_param_to_html_style(COLOR_BACKTICKS, "BACKTICKS"),
                          ansi_color_param_to_html_style("FG", "FG"),
                          ansi_color_param_to_html_style("BG", "BG"))
  } else if (OUTPUT_FORMAT == "LATEX") {
    LATEX_FOOTER = "\\end{alltt}\n\\end{varwidth}\n\\end{document}"
    # Is there a better way to store this?
    LATEX_HEADER = sprintf("\\documentclass{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage{xcolor}\n\\usepackage{alltt}\n\\usepackage[top=0cm, bottom=0cm, left=0cm, right=0cm]{geometry}\n\\usepackage{varwidth}\n\\usepackage[active,tightpage]{preview}\n\\usepackage[normalem]{ulem}\n\n\\setlength{\\fboxsep}{0pt}\n\n\\newcommand{\\bgcolor}[2]{\\colorbox{#1}{\\vphantom{Ay}#2}}\n\n\\PreviewEnvironment{varwidth}\n\n%s%s\\definecolor{color-attention}{HTML}{%s}\n\\definecolor{color-section}{HTML}{%s}\n\\definecolor{color-deprecated}{HTML}{%s}\n\\definecolor{color-default}{HTML}{%s}\n\\definecolor{color-warning}{HTML}{%s}\n\\definecolor{color-backticks}{HTML}{%s}\n\n\\pagestyle{empty}\n\\begin{document}\n\n\\begin{varwidth}{\\linewidth}\n%s%s\n\\begin{alltt}",
                           ansi_color_param_to_latex_color("FG", 1),
                           ansi_color_param_to_latex_color("BG", 1),
                           ansi_color_param_to_latex_color(COLOR_ATTENTION),
                           ansi_color_param_to_latex_color(COLOR_SECTION),
                           ansi_color_param_to_latex_color(COLOR_DEPRECATED),
                           ansi_color_param_to_latex_color(COLOR_DEFAULT),
                           ansi_color_param_to_latex_color(COLOR_WARNING),
                           ansi_color_param_to_latex_color(COLOR_BACKTICKS),
                           ansi_color_param_to_latex_color("FG"),
                           ansi_color_param_to_latex_color("BG"))
  }
}

# It would be nice to extract the options from the docstring of this script (there could
# be some sort of prefix before each option). Unfortunately, I can get the script passed
# with the -f flag only using gawk (so, names of options are hard-coded in print_help):
# for (key in PROCINFO["argv"]) {
#   if (PROCINFO["argv"][key] == "-f") {
#     printf PROCINFO["argv"][key + 1]
#   }
# }
function print_help() {
    print "Usage: awk [-v option=value] -f makefile-doc.awk [Makefile ...]"
    print "Description: Generate docs for Makefile variables and targets"
    print "Options:"
    printf "  OUTPUT_FORMAT: %s\n", OUTPUT_FORMAT
    printf "  EXPORT_THEME (theme for HTML/LATEX output): %s\n", EXPORT_THEME
    printf "  SUB (substitutions): %s\n", SUB
    printf "  TARGETS_REGEX (regex for matching targets): %s\n", TARGETS_REGEX
    printf "  VARIABLES_REGEX (regex for matching variables): %s\n", VARIABLES_REGEX
    printf "  VARS ([bool] show documented variables): %s\n", VARS
    printf "  PADDING (a padding character between anchors and docs): \"%s\"\n", PADDING
    printf "  DEPRECATED ([bool] show deprecated anchors): %s\n", DEPRECATED
    printf "  OFFSET (offset of docs from anchors): %s\n", OFFSET
    printf "  RECIPEPREFIX: %s\n", RECIPEPREFIX
    printf "  COLOR_: "
    printf "%sDEFAULT%s, ", COLOR_DEFAULT_CODE, COLOR_RESET_CODE
    printf "%sATTENTION%s, ", COLOR_ATTENTION_CODE, COLOR_RESET_CODE
    printf "%sDEPRECATED%s, ", COLOR_DEPRECATED_CODE, COLOR_RESET_CODE
    printf "%sSECTION%s, ", COLOR_SECTION_CODE, COLOR_RESET_CODE
    printf "%sWARNING%s, ", COLOR_WARNING_CODE, COLOR_RESET_CODE
    printf "%sBACKTICKS%s\n", COLOR_BACKTICKS_CODE, COLOR_RESET_CODE
}

# Initialize global variables.
BEGIN {
  STDERR = "/dev/stderr"
  if (UNIT_TEST) {
    exit
  }

  OUTPUT_FORMAT = OUTPUT_FORMAT == "" ? "ANSI" : toupper(OUTPUT_FORMAT)
  if (OUTPUT_FORMAT != "ANSI" && OUTPUT_FORMAT != "HTML" && OUTPUT_FORMAT != "LATEX") {
    printf("WARNING: ignorring invalid OUTPUT_FORMAT %s (using ANSI instead).\n",
           OUTPUT_FORMAT) > STDERR
    OUTPUT_FORMAT = "ANSI"
  }

  FS = ":" # set the field separator

  initialize_variables_regex()
  initialize_colors()

  RECIPEPREFIX = RECIPEPREFIX == 0 ? "^\t" : RECIPEPREFIX

  VARIABLES_REGEX = VARIABLES_REGEX == "" ? VARIABLES_REGEX_DEFAULT : VARIABLES_REGEX

  # Since we cannot use negative lookahead, (:|::)([^=:]|$)( *|.*;) simulates no = after
  # the last colon. We need to add a colon in the negative character class to prevent
  # matching e.g., x ::= 1
  #
  # Note: we have to use *(:|::) instead of *{1,2} because the latter doesn't work in mawk.
  TARGETS_REGEX = TARGETS_REGEX == "" ? "^ *[^#][ ,a-zA-Z0-9$_/%.(){}-]* *&?(:|::)([^=:]|$)( *|.*;)" : TARGETS_REGEX
  VARS = VARS == "" ? 1 : VARS
  PADDING = PADDING == "" ? " " : PADDING
  DEPRECATED = DEPRECATED == "" ? 1 : DEPRECATED
  OFFSET = OFFSET == "" ? 2 : OFFSET
  if (length(PADDING) != 1) {
    printf("ERROR: PADDING should have length 1\n") > STDERR
    exit 1
  }

  initialize_substitution_parameter_defaults()

  # initialize global arrays (i.e., hash tables) for clarity
  # index variables start from 1 because this is the standard in awk

  # map target name to description
  split("", TARGETS_DESCRIPTION_DATA)

  # map target name to section data
  # a section uses a targtet / variable as an anchor
  split("", TARGETS_SECTION_DATA)

  # the index for the next double-colon rule with description (the key doesn't include ~k)
  split("", TARGETS_DC_COUNTER)

  # map index to target name (order is important)
  split("", TARGETS)
  TARGETS_INDEX = 1

  # map index to line in description data (to be associated with the next anchor)
  split("", DESCRIPTION_DATA)
  DESCRIPTION_DATA_INDEX = 1

  # map index to line in section data (to be associated with the next anchor)
  split("", SECTION_DATA)
  SECTION_DATA_INDEX = 1

  # map variable name to description
  split("", VARIABLES_DESCRIPTION_DATA)

  # map variable name to section
  split("", VARIABLES_SECTION_DATA)

  # map index to variable name
  split("", VARIABLES)
  VARIABLES_INDEX = 1

  split("", DISPLAY_PARAMS)

  split("\\.PHONY \\.SILENT \\.IGNORE \\.SECONDARY \\.INTERMEDIATE \\.PRECIOUS",
        IGNORED_TARGETS,
        " ")

  HEADER_TARGETS = "Available targets:"
  HEADER_VARIABLES = "Command-line arguments:"
  NUMBER_OF_FILES_PROCESSED = 0
  FILES_PROCESSED = ""
  SPACES_TABS_REGEX = "^[ \t]+|[ \t]+$"

  # used to decorate double-colon targets in the documentation
  DOUBLE_COLON_SEPARATOR = "~"

  IN_MULTILINE_BACKSLASH_COMMENT = 0
  IN_MULTILINE_BACKSLASH_COMMAND = 0
  IN_DEFINE_ENDEF_BLOCK = 0
  IN_RULE = ""

  # we could exit faster but this causes the linter to not see defined variables
  SHOW_HELP = SHOW_HELP == "" ? 1 : SHOW_HELP  # to suppress during linting
  if (ARGC == 1) {
    if (SHOW_HELP) {
      print_help()
    }
    exit 1
  }
}

FNR == 1 {
  NUMBER_OF_FILES_PROCESSED++
  if (FILES_PROCESSED) {
    FILES_PROCESSED = FILES_PROCESSED " " FILENAME
  } else {
    FILES_PROCESSED = FILENAME
  }
}

# Skip backslash multiline comments
# FIXME: at some point we might allow for them to constitute anchor documentation
#        but for the moment they are simply ignored
/^ *#[^\\]*?([\\]{2})*\\$/ || IN_MULTILINE_BACKSLASH_COMMENT {
  if (!IN_MULTILINE_BACKSLASH_COMMENT) {
    IN_MULTILINE_BACKSLASH_COMMENT = 1
  } else if (!($0 ~ /^[^\\]*?([\\]{2})*\\$/)) {
    IN_MULTILINE_BACKSLASH_COMMENT = 0
  }

  next
}

# This has no effect for now
/^ *define */ || IN_DEFINE_ENDEF_BLOCK {
  if (!IN_DEFINE_ENDEF_BLOCK) {
    IN_DEFINE_ENDEF_BLOCK = 1
  } else if ($0 ~ /^ *endef$/) {
    IN_DEFINE_ENDEF_BLOCK = 0
  }
}

IN_RULE && $0 ~ RECIPEPREFIX || IN_MULTILINE_BACKSLASH_COMMAND {
  forget_descriptions_data()

  # match odd number of slashes at the end
  if ($0 ~ sprintf("%s[^\\\\]*?([\\\\]{2})*\\\\$", RECIPEPREFIX)) {
    IN_MULTILINE_BACKSLASH_COMMAND = 1
  } else {
    IN_MULTILINE_BACKSLASH_COMMAND = 0
  }

  next
}

{
  PATTERN_RULE_MATCHED = 0
}

# Capture the line if it is a description (but not a section).
/^ *##([^@]|$)/ {
  g_description_string = $0
  sub(/^ */, "", g_description_string)

  save_description_data(g_description_string)

  PATTERN_RULE_MATCHED = 1
}

# Flush accumulated descriptions if followed by an empty line
/^$/ {
  PATTERN_RULE_MATCHED = 1
}

# New section (all lines in a multi-line sections should start with ##@)
/^ *##@/ {
  g_section_string = $0
  sub(/ *##@/, "", g_section_string) # strip the tags (they are not needed anymore)

  save_section_data(g_section_string)

  PATTERN_RULE_MATCHED = 1
}

$0 ~ TARGETS_REGEX {
  if (detect_ignored_targets($0)) {
    next
  }

  if (length_array_posix(DESCRIPTION_DATA) == 0) {
    parse_inline_descriptions($0)
  }

  # remove spaces up to & in grouped targets, e.g., `t1 t2   &` becomes `t1 t2&`
  # for the reason to use \\&, see:
  # https://www.gnu.org/software/gawk/manual/html_node/Gory-Details.html
  g_target_name_nominal = $1
  sub(/ *&/, "\\&", g_target_name_nominal)

  if (length_array_posix(DESCRIPTION_DATA) > 0) {
    g_target_name = ($0 ~ "::") ? form_dc_target_name(g_target_name_nominal) : g_target_name_nominal

    TARGETS_INDEX = associate_data_with_anchor(strip_start_end_spaces_tabs(g_target_name),
                                               TARGETS,
                                               TARGETS_INDEX,
                                               TARGETS_DESCRIPTION_DATA,
                                               TARGETS_SECTION_DATA,
                                               "target")
    TARGETS_DC_COUNTER[g_target_name_nominal]++
  }

  IN_RULE = g_target_name_nominal
  PATTERN_RULE_MATCHED = 1
}

$0 ~ VARIABLES_REGEX {
  if (length_array_posix(DESCRIPTION_DATA) == 0) {
    parse_inline_descriptions($0)
  }

  if (length_array_posix(DESCRIPTION_DATA) > 0) {
    g_variable_name = strip_start_end_spaces_tabs(parse_variable_name($0))
    VARIABLES_INDEX = associate_data_with_anchor(g_variable_name,
                                                 VARIABLES,
                                                 VARIABLES_INDEX,
                                                 VARIABLES_DESCRIPTION_DATA,
                                                 VARIABLES_SECTION_DATA,
                                                 "variable")
  }

  IN_RULE = ""
  PATTERN_RULE_MATCHED = 1
}

# keep here for debugging purposes (it is commented-out because of a goawk bug)
# PATTERN_RULE_MATCHED == 0 {
#
# }

# Display results (all stdout is here).
END {
  if (UNIT_TEST) {
    exit 0
  }
  form_substitutions() # form SUB_LABELS before calling get_max_anchor_length

  g_max_target_length = get_max_anchor_length(TARGETS)
  g_max_variable_length = get_max_anchor_length(VARIABLES)
  g_max_anchor_length = max(g_max_target_length, g_max_variable_length)
  g_separator = get_separator("-", g_max_anchor_length)

  if (OUTPUT_FORMAT == "HTML") {
    print(HTML_HEADER)
  } else if (OUTPUT_FORMAT == "LATEX") {
    print(LATEX_HEADER)
  }

  # process targets
  if (g_max_target_length > 0) {
    printf("%s\n%s\n%s\n", g_separator, HEADER_TARGETS, g_separator)

    for (g_indx = 1; g_indx <= length_array_posix(TARGETS); g_indx++) {
      g_target = TARGETS[g_indx]
      g_description = format_description_data(g_target,
                                              TARGETS_DESCRIPTION_DATA,
                                              g_max_anchor_length)
      g_section = get_associated_section_data(g_target, TARGETS_SECTION_DATA)
      display_anchor_with_data(g_target, g_description, g_section, g_max_anchor_length)
    }
  }

  # process variables
  # when all variables are deprecated and DEPRECATED = 0, just a header is displayed
  if (g_max_variable_length > 0 && VARS) {
    g_variables_display_pattern = g_max_target_length > 0 ? "\n%s\n%s\n%s\n": "%s\n%s\n%s\n"

    printf(g_variables_display_pattern, g_separator, HEADER_VARIABLES, g_separator)
    for (g_indx = 1; g_indx <= length_array_posix(VARIABLES); g_indx++) {
      g_variable = VARIABLES[g_indx]
      g_description = format_description_data(g_variable,
                                              VARIABLES_DESCRIPTION_DATA,
                                              g_max_anchor_length)
      g_section = get_associated_section_data(g_variable, VARIABLES_SECTION_DATA)
      display_anchor_with_data(g_variable, g_description, g_section, g_max_anchor_length)
    }
  }

  if (g_max_target_length > 0 || (g_max_variable_length > 0 && VARS)) {
    printf("%s\n", g_separator)
  } else {
    if (NUMBER_OF_FILES_PROCESSED > 0) {
      printf("WARNING: no documented targets/variables in %s\n",
             FILES_PROCESSED) > STDERR
    }
  }

  if (OUTPUT_FORMAT == "HTML") {
    print(HTML_FOOTER)
  } else if (OUTPUT_FORMAT == "LATEX") {
    print(LATEX_FOOTER)
  }
}
