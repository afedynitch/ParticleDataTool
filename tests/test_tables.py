import particletools
from particletools import tables
import os
import xml.etree.ElementTree as ET
from fractions import Fraction
from math import isnan
from six import StringIO

def nan_equal(a, b):
    if isnan(a) and isnan(b):
        return True
    return a == b

# inject equality operator into ParticleData class for testing
tables.ParticleData.__eq__ = lambda a, b: (
        a.name == b.name and nan_equal(a.mass, b.mass) and
        a.charge == b.charge and nan_equal(a.ctau, b.ctau)
    )


def test_PYTHIAParticleData_against_xml_database():
    pdg = tables.PYTHIAParticleData(use_cache=False)

    path = os.path.dirname(os.path.abspath(particletools.__file__))
    xmlname = path + "/ParticleData.xml"
    assert os.path.exists(xmlname)
    root = ET.parse(xmlname).getroot()

    # test consistency with XML database
    first_name = set()
    for child in root:
        # particle names are not unique in XML, e.g. two entries are called
        # "Graviton" with id = 39 (official) and id = 5000039 (?)
        # When names are not unique, the first entry in XML is returned.
        # Mapping from id to name must always work.
        if child.tag != 'particle': continue
        attr = child.attrib
        pid = int(attr['id'])
        name = attr['name']
        mass = float(attr['m0'])
        charge = float(attr['chargeType']) / 3.0
        assert pdg.name(pid) == name
        assert pdg.mass(pid) == mass
        assert pdg.charge(pid) == charge

        if 'tau0' in attr:
            assert pdg.ctau(pid) == float(attr['tau0']) * 0.1

        if name not in first_name:
            assert pdg.pdg_id(name) == pid
            assert pdg.mass(name) == mass
            assert pdg.charge(name) == charge
        first_name.add(name)


def test_PYTHIAParticleData_cache():
    pdg_xml = tables.PYTHIAParticleData(use_cache=False)
    # make sure cache is used
    tables.PYTHIAParticleData(use_cache=True)
    pdg = tables.PYTHIAParticleData(use_cache=True)
    assert tuple(pdg_xml.iteritems()) == tuple(pdg.iteritems())


def test_PYTHIAParticleData_force_stable():
    pdg = tables.PYTHIAParticleData()
    pdg2 = tables.PYTHIAParticleData()

    pids = (13, 15, -13, -15)

    for pid in pids:
        pdg._force_stable(pid) # may not affect other instances of table
    for pid in pids:
        assert pdg.ctau(pid) == float("Inf")
        assert pdg.ctau(pid) != pdg2.ctau(pid)


def test_print_stable():
    buf = StringIO()
    tables.print_stable(1e-10, file=buf)
    buf.seek(0)
    assert buf.read() == """Known particles which lifetimes longer than 1e-10 s:
Name                  ctau [cm]   PDG ID
Sigma-                     4.43     3112
Sigmabar+                  4.43    -3112
Xi-                        4.91     3312
Xibar+                     4.91    -3312
Lambda0                    7.89     3122
Lambdabar0                 7.89    -3122
Xi0                        8.71     3322
Xibar0                     8.71    -3322
K+                          371      321
K-                          371     -321
pi+                         780      211
pi-                         780     -211
K_L0                   1.53e+03      130
mu+                    6.59e+04      -13
mu-                    6.59e+04       13
n0                     2.66e+13     2112
nbar0                  2.66e+13    -2112
"""


def test_print_decay_channels():
    kaon = 321
    buf = StringIO()
    tables.print_decay_channels(kaon, file=buf)
    buf.seek(0)
    assert(buf.read() == """K+ decays into:
\t     63.43%, mu+, nu_mu
\t    20.911%, pi+, pi0
\t      5.59%, pi+, pi+, pi-
\t      4.98%, nu_e, e+, pi0
\t      3.32%, nu_mu, mu+, pi0
\t     1.757%, pi+, pi0, pi0
\t    0.0041%, e+, nu_e, pi+, pi-
\t    0.0028%, mu+, nu_mu, pi+, pi-
\t    0.0022%, e+, nu_e, pi0, pi0
\t    0.0015%, e+, nu_e
\t    0.0014%, mu+, nu_mu, pi0, pi0
""")


def test_make_stable_list():
    assert tables.make_stable_list(1e-6) == [
            13, 2112, 7013, -7313, 7113, -7213, 7313,
            -7013, -7113, 7213, -2112, -13
        ]
