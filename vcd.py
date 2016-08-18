# -*- coding: utf-8 -*-
"""
Created on Thu Aug 28 11:35:25 2014

@author: markgot
"""
import time
import sys
import os.path
import os

__version__ = "1.0"

class var():
    """
Variable object.
holds the changes done to the variable with time

Parameters
--------
name : name of the variable
bits : number of bits in the variable
wire : not implemented

Examples
-------
A sweeping clock

>>> from vcd import var
>>> v = var('clk')
>>> v.append('0', 0)
>>> v.append(1, 1)
>>> v.append([0,1], [2,3])
>>> v.append(['0', '1'], [4, 5])
>>> v.append([0, 1]*50, range(6, 106))
"""

    def __init__(self, name, bits=1, wire=True):
        self._name = name
        self._bits = bits
        self._wire = wire
        self._data = []
        self._char = ''

    def append(self, data, time, timeFromLast=True):
        """
Appends changes to variable state over time.
The 'time' variable is how long since the last change.
If arrays of values are appended both arrays MUST be of the same length. \n
Parameters:
--------
data : array or single input
    single point - 0,1,'0','1','x','z'\n
    set of points - [0,1,0] ,['0','x','z','0']\n
time : array or single input
    single point - number of # from last\n
    set of points - set of times when data is also a list\n
Examples:
--------
>>> from vcd import var
>>> v = var('clk')
>>> v.append('0', 0)
>>> v.append(1, 1)
>>> v.append([0,1], [2,3])
>>> v.append(['0', '1'], [4, 5])
>>> v.append([0, 1]*50, range(6, 106))
        """
        if (type(data) is int or type(data) is str) and type(time) is int:
            if type(data) is int:
                data = str(data)
            self._data.append((data, time))
            return 'succses'

        elif type(data) is list and type(time) is list:
            if len(data) != len(time):
                return 'list lengths do not equal'
            for i in xrange(len(data)):
                if type(data[i]) is int:
                    data[i] = str(data[i])
                self._data.append((data[i], time[i]))
            return 'succes'
        else:
            return 'failure in appending data'


class scope:
    """
scope object
holds a module object that can contain variables

Parameter
------
name : name of the module

Example
------
>>> from vcd import var,scope
>>> v = var('clk')
>>> v.append([0,1]*50, range(100))
>>> s = scope('uut')
>>> s.addvar(v)

"""
    def __init__(self, name):
        self._name = name
        self._scopelist = []
        self._varlist = []

    def addvar(self, var):
        if var.__class__.__name__ is not 'var':
            return 'bad var'
        self._varlist.append(var)
        return

    def addscope(self, scope):
        if scope.__class__.__name__ is not 'scope':
            return 'bad scope'
        self._scopelist.append(scope)
        return

    def getvar(self, iname):
        """
gets variable by name or index\n
Parameter
--------
iname : either the index of the var in scope or it's name\n
        """
        if type(iname) is int:
            return self._varlist[iname]
        if type(iname) is str:
            for i in self._varlist:
                if i._name == iname:
                    return i
        return 'var not found'


class vcd:
    """
create a 'fake' vcd file that can be opened as a didgital waveform
from raw data

Examples
------
>>> import vcd
>>> vc = vcd.vcd()
>>> clk = vcd.var('clk')
>>> data = vcd.var('data')
>>> uut = vcd.scope('uut')\n
>>> uut.addvar(clk)
>>> uut.addvar(data)
>>> vc.addscope(uut)\n
>>> clk.append([0,1]*5, [1]*10) # array length of data and time must equal
>>> data.append([0,1,'x',1,0]*2, [1]*10)
>>> vc.savefile(filename='my_vcd')
"""
    def __init__(self):
        self._filename = 'vcd_test'
        self._suffix = 'vcd'
        self._version = 'py_vcd'
        self._timescale_num = 1
        self._timescale_unit = 'ps'
        self._filedilimiter = '\\'
        self._scopelist = []

    def constructFileString(self):
        st = ''
        st += "$date\n\t"+time.asctime()+"\n$end\n"
        st += "$version\n\t"+self._version+"\n$end\n"
        st += "$timescale\n\t"+str(self._timescale_num)+self._timescale_unit+"\n$end\n"
        varlist = []
        indexlist = []
        counterlist = []
        for i in self._scopelist:  # need to switch with something recursive
            st += "$scope module "+i._name+" $end\n"
            for j in range(len(i._varlist)):
                varlist.append(i.getvar(j))
                tempvar = i.getvar(j)
                tempvar._char = chr(len(varlist)-1+33)
                st += "$var wire "+str(tempvar._bits)+" "+tempvar._char+" "+tempvar._name+" $end\n"
            st += "$upscope $end\n"
        st += "$enddefinitions $end\n"
        st += "$dumpvars\n"
        st += "#0\n"
        #TODO from here figure out how to do the timing
        indexlist = [0]*len(varlist)
        counterlist = [0]*len(varlist)
        counttime = 0
        change = False
        #tempvalue = 0
        tempvalue = ''
        temptxt = ''
        while not all(-1 == item for item in indexlist):
            for i in xrange(len(varlist)):
                if(indexlist[i] < len(varlist[i]._data) and indexlist[i] != -1):
                    if counterlist[i] == varlist[i]._data[indexlist[i]][1]:
                        if indexlist[i]+1 == len(varlist[i]._data):
                            indexlist[i] = -1
                        else:
                            indexlist[i] += 1
                            change = True
                            if varlist[i]._bits == 1:
                                tempvalue = varlist[i]._data[indexlist[i]][0]
                            else:
                                tempvalue = 'b'+(formatint(varlist[i]._data[indexlist[i]][0]), '0' + str(varlist[i]._bits) + 'b') + ' '
                            temptxt += tempvalue+varlist[i]._char+"\n"
                        counterlist[i] = 0
                    else:
                        counterlist[i] = counterlist[i] + 1
                else:
                    indexlist[i] = -1
            if change is True:
                st += "#"+str(counttime)+"\n"+temptxt
                temptxt = ''
                change = False
            counttime = counttime + 1

        return st

    def addscope(self, scope):
        if scope.__class__.__name__ is not 'scope':
            return 'bad scope'
        self._scopelist.append(scope)
        return

    def savefile(self, path='.', filename=''):
        """Saves the vcd file based on all the vars and scopes filled in the vcd object.\n
Parameter
--------
path : the folder path in which to save the vcd file. can be relative to working file or absolute.
filename : the name of the file.
        """
        if filename == '':
            filename = self._filename
        fullpath = path + os.sep + filename + '.' + self._suffix
        if os.path.isfile(fullpath):
            print 'the file already exists. do want to write over it? [Y/N]'
            ans = sys.stdin.readline()
            if ans.find('Y') != -1 or ans.find('y') != -1:
                open(fullpath, 'w').close()  # erase previos contents of file
                file = open(fullpath, 'w')
                file.write(self.constructFileString())
                file.close()
                return
            else:
                return
        else:
            file = open(fullpath, 'w')
            file.write(self.constructFileString())
            file.close()
            return
