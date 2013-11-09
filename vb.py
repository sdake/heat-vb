#!/usr/bin/env python

import hashlib
import json
import os
import subprocess
import uuid
import yaml

def parse(template):
    return yaml.safe_load(template)

class CommandRunner(object):
    """Helper class to run a command and store the output."""

    def __init__(self, command, nextcommand=None):
        self._command = command
        self._next = nextcommand
        self._stdout = None
        self._stderr = None
        self._status = None

    def __str__(self):
        s = "CommandRunner:"
        s += "\n\tcommand: %s" % self._command
        if self._status:
            s += "\n\tstatus: %s" % self.status
        if self._stdout:
            s += "\n\tstdout: %s" % self.stdout
        if self._stderr:
            s += "\n\tstderr: %s" % self.stderr
        return s

    def run(self, cwd=None, env=None):
        """Run the Command and return the output.

        Returns:
            self
        """
        subproc = subprocess.Popen(self._command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, cwd=cwd, env=env, shell=True)
        output = subproc.communicate()

        self._status = subproc.returncode
        self._stdout = output[0]
        self._stderr = output[1]
        return self

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    @property
    def status(self):
        return self._status

template_file = open('OpenShift.yaml', 'r')
template_yaml = parse(template_file)
m = hashlib.md5()
m.update(yaml.dump(template_yaml))
dib_name = 'dib_' + m.hexdigest() 

outfile_name = 'OpenShiftDib.yaml'
new_yaml = open(outfile_name, 'w')

for res in template_yaml['resources']:
    if template_yaml['resources'][res]['type'] == 'OS::Nova::Server':
        print "Creating image for resource %s" % res
        cmd = "/usr/bin/virt-builder -o " + dib_name + "_" + res + " fedora-19 --install cloud-init,heat-cfntools --mkdir /var/lib/heat-cfntools --write /var/lib/heat-cfntools/cfn-init-data:'" + json.dumps(template_yaml['resources'][res]['Metadata']) + "' --run-command 'yum -y update' --run-command '/usr/bin/cfn-init' --run-command 'passwd -l root'"

        c = CommandRunner(cmd)
        c.run()
#        print '%s' % c.stdout()

        del template_yaml['resources'][res]['Metadata']
        template_yaml['resources'][res]['properties']['image'] = "'" + dib_name + res + "'"

# output new template
print 'Writing new template in %s.' % outfile_name
new_yaml.write(yaml.dump(template_yaml))
