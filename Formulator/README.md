# Embedded Formulator Runtime

This directory is a trimmed runtime derived from
[Formulator](https://github.com/kerdevils/Formulator). It contains the JCL
parser, damage analyzer, shared models and kungfu source modules required by
JX3-JCL-Service.

The upstream desktop UI, equipment editor, asset generators and release
workflows are intentionally excluded. Only Wufang (10627) is imported and
registered at service startup. Other kungfu source directories are retained so
they can be integrated later by explicitly importing the module and adding a
`Kungfu` entry to `SUPPORT_KUNGFU` in `kungfus/__init__.py`.
