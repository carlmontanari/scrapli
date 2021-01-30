<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>


<%def name="variable(var)" buffered="True">
    <%
        annot = show_type_annotations and var.type_annotation() or ''
        if annot:
            annot = ': ' + annot
    %>
`${var.name}${annot}`

% if var.docstring:
```text
${var.docstring}
```
% endif

</%def>

<%def name="function(func)" buffered="True">
    <%
        returns = show_type_annotations and func.return_annotation() or ''
        if returns:
            returns = ' \N{non-breaking hyphen}> ' + returns
    %>

<%text>#### </%text>${func.name}
`${func.name}(${", ".join(func.params(annotate=show_type_annotations))})${returns}`

% if func.docstring:
```text
${func.docstring}
```
% endif

</%def>

<%def name="method(meth)" buffered="True">
    <%
        returns = show_type_annotations and meth.return_annotation() or ''
        if returns:
            returns = ' \N{non-breaking hyphen}> ' + returns
    %>

<%text>##### </%text>${meth.name}
`${meth.name}(${", ".join(meth.params(annotate=show_type_annotations))})${returns}`

% if meth.docstring:
```text
${meth.docstring}
```
% endif

</%def>


<%def name="class_(cls)" buffered="True">
<%text>### </%text>${cls.name}


% if cls.docstring:
```text
${cls.docstring}
```
% endif

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
${cls.source}
        </code>
    </pre>
</details>

<%
  class_vars = cls.class_variables(show_inherited_members, sort=sort_identifiers)
  static_methods = cls.functions(show_inherited_members, sort=sort_identifiers)
  inst_vars = cls.instance_variables(show_inherited_members, sort=sort_identifiers)
  methods = cls.methods(show_inherited_members, sort=sort_identifiers)
  mro = cls.mro()
  subclasses = cls.subclasses()
%>
% if mro:
<%text>#### Ancestors (in MRO)</%text>
    % for c in mro:
- ${c.refname}
    % endfor
% endif
% if subclasses:
<%text>#### Descendants</%text>
    % for c in subclasses:
- ${c.refname}
    % endfor
% endif
% if class_vars:
<%text>#### Class variables</%text>
    % for v in class_vars:
${variable(v)}
    % endfor
% endif
% if static_methods:
<%text>#### Static methods</%text>
    % for f in static_methods:
${function(f)}
    % endfor
% endif
% if inst_vars:
<%text>#### Instance variables</%text>
    % for v in inst_vars:
${variable(v)}
    % endfor
% endif
% if methods:
<%text>#### Methods</%text>
    % for m in methods:
${method(m)}
    % endfor
% endif
</%def>


## Start the output logic for an entire module.

<%
  variables = module.variables(sort=sort_identifiers)
  classes = module.classes(sort=sort_identifiers)
  functions = module.functions(sort=sort_identifiers)
  submodules = module.submodules()
%>

<%text>#Module </%text>${module.name}

${module.docstring}

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
${module.source}
        </code>
    </pre>
</details>


## % if submodules:
## <%text>## Sub-modules</%text>
##     % for m in submodules:
## * ${m.name}
##     % endfor
## % endif
##
## % if variables:
## <%text>## Variables</%text>
##     % for v in variables:
## ${variable(v)}
##
##     % endfor
## % endif
##
## % if functions:
## <%text>## Functions</%text>
##     % for f in functions:
## ${function(f)}
##
##     % endfor
## % endif

% if classes:
<%text>## Classes</%text>
    % for c in classes:
${class_(c)}

    % endfor
% endif
