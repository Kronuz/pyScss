#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
from os.path import exists
from os import stat, system
from glob import glob

########################################
# Platform dependent configuration
########################################

config = {
    'ld': 'gcc',
    'ld_flags': '-shared',
    'shared_ext': 'so',
    'shared_oflag': '-o ',
    'obj_ext': 'o',
    'cc': 'gcc',
    'cc_flags': '-fPIC -O3 -c',
}

if sys.platform == 'win32':
    # use Microsoft compiler
    config['ld'] = 'link'
    config['ld_flags'] = '/DLL /NOLOGO /OPT:REF /OPT:ICF /LTCG /DYNAMICBASE /NXCOMPAT'
    config['shared_ext'] = 'dll'
    config['shared_oflag'] = '/OUT:'
    config['obj_ext'] = 'obj'
    config['cc'] = 'cl'
    config['cc_flags'] = '/O3 /Oi /GL /EHsc /Gy /W3 /nologo /c'


def need_update(obj, src):
    if not exists(obj):
        return True
    tobj = stat(obj).st_mtime
    tsrc = stat(src).st_mtime
    if tobj < tsrc:
        return True
    return False


def do_cmd(cmd):
    print cmd
    system(cmd)


def compile_obj(name):
    obj = '%s.%s' % (name, config['obj_ext'])
    src = '%s.c' % name

    if need_update(obj, src):
        do_cmd('%s %s %s' % (config['cc'], config['cc_flags'], src))


def link(name, objs):
    so = '%s.%s' % (name, config['shared_ext'])
    for obj in objs:
        if need_update(so, obj):
            do_cmd('%s %s %s%s %s' %
               (config['ld'],
                config['ld_flags'],
                config['shared_oflag'],
                so,
                ' '.join(objs)),
            )
            break

if __name__ == '__main__':
    srcs = glob('*.c')
    names = [re.sub(r'\.c$', '', name) for name in srcs]

    for name in names:
        compile_obj(name)
    link('_scss_c', ['%s.%s' % (name, config['obj_ext']) for name in names])
