#!/usr/bin/env python
#unit tests for util.py

from os.path import split, abspath
from cogent.util.unit_test import TestCase, main
from cogent.parse.fasta import MinimalFastaParser
from cogent.app.util import get_tmp_filename
from cogent.util.misc import remove_files
from qiime.util import make_safe_f, FunctionWithParams, qiime_blast_seqs,\
    extract_seqs_by_sample_id, build_blast_db_from_fasta_file, \
    get_qiime_project_dir, parse_qiime_config_files


__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2010, The QIIME Project"
#remember to add yourself if you make changes
__credits__ = ["Rob Knight", "Daniel McDonald","Greg Caporaso"] 
__license__ = "GPL"
__version__ = "1.0-dev"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"
__status__ = "Pre-release"

class TopLevelTests(TestCase):
    """Tests of top-level module functions."""

    def test_make_safe_f(self):
        """make_safe_f should return version of f that ignores extra kwargs."""
        def f(x,y): return x*y
        self.assertEqual(f(3,4), 12)
        g = make_safe_f(f, ['x','y'])
        self.assertEqual(g(3,4), 12)
        self.assertEqual(g(x=3,y=4,z=10,xxx=11), 12)
        
    def test_extract_seqs_by_sample_id(self):
        """extract_seqs_by_sample_id: functions as expected """
        
        seqs = [('Samp1_109','ACGG'),\
                ('Samp1_110','CCGG'),\
                ('samp1_109','GCGG'),\
                ('S2','AA'),\
                ('S3','CC'),\
                ('S4','GG'),\
                ('S44','TT'),\
                ('S4','TAAT')]
        sample_ids = ['Samp1','S44']
        expected = [('Samp1_109','ACGG'),\
                    ('Samp1_110','CCGG'),\
                    ('S44','TT')]
        actual = list(extract_seqs_by_sample_id(seqs,sample_ids))
        self.assertEqual(actual,expected)
        
        #negated
        expected_neg = [('samp1_109','GCGG'),\
                ('S2','AA'),\
                ('S3','CC'),\
                ('S4','GG'),\
                ('S4','TAAT')]
        actual = list(extract_seqs_by_sample_id(seqs,sample_ids,negate=True))
        self.assertEqual(actual,expected_neg)
        
        # OK if user passes dict of sample ids
        sample_ids = {'samp1':25}
        expected = [('samp1_109','GCGG')]
        actual = list(extract_seqs_by_sample_id(seqs,sample_ids))
        self.assertEqual(actual,expected)
        
    def test_get_qiime_project_dir(self):
        """getting the qiime project directory functions as expected """
        actual = get_qiime_project_dir()
        # note that although expected it being computed in the same way as
        # actual in get_qiime_project_dir(), the value for __file__ is 
        # different here.
        cwd = split(__file__)[0]
        if not cwd:
            expected = abspath('..')
        else:
            expected = abspath(cwd+'/..')
        self.assertEqual(actual,expected)
        
    def test_parse_qiime_config_files(self):
        """ parse_qiime_config_files functions as expected """
        fake_file1 = ['key1\tval1','key2\tval2']
        fake_file2 = ['key2\tval3']
        actual = parse_qiime_config_files([fake_file1,fake_file2])
        expected = {'key1':'val1','key2':'val3'}
        self.assertEqual(actual,expected)
        
        # looking up a non-existant value returns None
        self.assertEqual(actual['fake_key'],None)
        
        # empty dict on empty input
        self.assertEqual(parse_qiime_config_files([]),{})

class FunctionWithParamsTests(TestCase):
    """Tests of the FunctionWithParams class.

    Note: FunctionWithParams itself is abstract, so need to subclass here."""

    def setUp(self):
        """Set up standard items for testing."""
        class FWP(FunctionWithParams):
            Name = 'FWP'
            t = True
            _tracked_properties = ['t']
            def getResult(self):
                return 3
        self.FWP = FWP

    def test_init(self):
        """FunctionWithParams __init__ should be successful."""
        x = self.FWP({'x':3})
        self.assertEqual(x.Name, 'FWP')
        self.assertEqual(x.Params, {'x':3})

    def test_str(self):
        """FunctionWithParams __str__ should produce expected string"""
        x = self.FWP({'x':3})
        lines = ['FWP parameters:','t:True','Application:None',\
                'Algorithm:None','Citation:None','x:3']
        self.assertEqual(str(x), '\n'.join(lines))

    def test_call(self):
        """FunctionWithParams __str__ should produce expected string"""
        x = self.FWP({'x':3})
        self.assertEqual(x(), 3)

    def test_formatResult(self):
        """FunctionWithParams formatResult should produce expected format"""
        x = self.FWP({'x':3})
        self.assertEqual(x.formatResult(3), '3')

class BlastSeqsTests(TestCase):
    """ Tests of the qiime_blast_seqs function (will move to PyCogent eventually)
    """

    def setUp(self):
        """ 
        """
        self.refseqs1 = refseqs1.split('\n')
        self.inseqs1 = inseqs1.split('\n')
        self.blast_db, db_files_to_remove =\
          build_blast_db_from_fasta_file(self.refseqs1,output_dir='/tmp/')
        self.files_to_remove = db_files_to_remove
        
        self.refseqs1_fp = get_tmp_filename(\
         tmp_dir='/tmp/', prefix="BLAST_temp_db_", suffix=".fasta")    
        fasta_f = open(self.refseqs1_fp,'w')
        fasta_f.write(refseqs1)
        fasta_f.close()
        
        self.files_to_remove = db_files_to_remove + [self.refseqs1_fp]
          
    def tearDown(self):
        remove_files(self.files_to_remove)
        
    def test_w_refseqs_file(self):
        """qiime_blast_seqs functions with refseqs file 
        """
        inseqs = MinimalFastaParser(self.inseqs1)
        actual = qiime_blast_seqs(inseqs,refseqs=self.refseqs1)
        self.assertEqual(len(actual),5)
        
        # couple of sanity checks against command line blast
        self.assertEqual(actual['s2_like_seq'][0][0]['SUBJECT ID'],'s2')
        self.assertEqual(actual['s105'][0][2]['SUBJECT ID'],'s1')
        
    def test_w_refseqs_fp(self):
        """qiime_blast_seqs functions refseqs_fp
        """
        inseqs = MinimalFastaParser(self.inseqs1)
        actual = qiime_blast_seqs(inseqs,refseqs_fp=self.refseqs1_fp)
        self.assertEqual(len(actual),5)
        
        # couple of sanity checks against command line blast
        self.assertEqual(actual['s2_like_seq'][0][0]['SUBJECT ID'],'s2')
        self.assertEqual(actual['s105'][0][2]['SUBJECT ID'],'s1')
    
    def test_w_preexising_blastdb(self):
        """qiime_blast_seqs functions with pre-existing blast_db
        """        
        # pre-existing blast db
        inseqs = MinimalFastaParser(self.inseqs1)
        actual = qiime_blast_seqs(inseqs,blast_db=self.blast_db)
        self.assertEqual(len(actual),5)
        
        # couple of sanity checks against command line blast
        self.assertEqual(actual['s2_like_seq'][0][0]['SUBJECT ID'],'s2')
        self.assertEqual(actual['s105'][0][2]['SUBJECT ID'],'s1')
    
    def test_w_alt_seqs_per_blast_run(self):
        """qiime_blast_seqs: functions with alt seqs_per_blast_run
        """
        for i in range(1,20):
            inseqs = MinimalFastaParser(self.inseqs1)
            actual = qiime_blast_seqs(\
             inseqs,blast_db=self.blast_db,seqs_per_blast_run=i)
            self.assertEqual(len(actual),5)
    
            # couple of sanity checks against command line blast
            self.assertEqual(actual['s2_like_seq'][0][0]['SUBJECT ID'],'s2')
            self.assertEqual(actual['s105'][0][2]['SUBJECT ID'],'s1')
            
    def test_alt_blast_param(self):
        """qiime_blast_seqs: alt blast params give alt results"""
        # Fewer blast hits with stricter e-value
        inseqs = MinimalFastaParser(self.inseqs1)
        actual = qiime_blast_seqs(inseqs,blast_db=self.blast_db,params={'-e':'1e-4'})
        # NOTE: A BUG (?) IN THE BlastResult OR THE PARSER RESULTS IN AN EXTRA
        # BLAST RESULT IN THE DICT (actual HERE) WITH KEY ''
        
        self.assertTrue('s2_like_seq' in actual)
        self.assertFalse('s100' in actual)
        
    def test_error_on_bad_param_set(self):
        inseqs = MinimalFastaParser(self.inseqs1)
        # no blastdb or refseqs
        self.assertRaises(AssertionError,qiime_blast_seqs,inseqs)
        
inseqs1 = """>s2_like_seq
TGCAGCTTGAGCACAGGTTAGAGCCTTC
>s100
TGCAGCTTGAGCACAGGTTAGCCTTC
>s101
TGCAGCTTGAGCACAGGTTTTTCAGAGCCTTC
>s104
TGCAGCTTGAGCACAGGTTAGCCTTC
>s105
TGCAGCTTGAGCACAGGTTAGATC"""
        
refseqs1 = """>s0
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
>s1
TGCAGCTTGAGCCACAGGAGAGAGAGAGCTTC
>s2
TGCAGCTTGAGCCACAGGAGAGAGCCTTC
>s3
TGCAGCTTGAGCCACAGGAGAGAGAGAGCTTC
>s4
ACCGATGAGATATTAGCACAGGGGAATTAGAACCA
>s5
TGTCGAGAGTGAGATGAGATGAGAACA
>s6
ACGTATTTTAATTTGGCATGGT
>s7
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
>s8
CCAGAGCGAGTGAGATAGACACCCAC
"""



#run unit tests if run from command-line
if __name__ == '__main__':
    main()
