"""
    Module with for building variant objects from a vcf
"""
import logging

from cyvcf2 import VCF

from mutacc.parse.path_parse import parse_path


#IDs in the INFO field that should be included in the database
INFO_IDS = (

    'RankScore',

)

GENE_INFO = ('hgnc_symbol',
             'region_annotation',
             'functional_annotation',
             'sift_prediction',
             'polyphen_prediction')
ANNOTATION = 'ANN'

LOG = logging.getLogger(__name__)


class Variant(dict):

    """
        Class to represent variant
    """

    def __init__(self, vcf_entry, samples, padding, parse_info, rank_model_version=None):

        super(Variant, self).__init__()

        self.entry = vcf_entry
        self.samples = samples

        self.build_variant_object(padding, rank_model_version=rank_model_version)
        self.entry = str(self.entry)
        ##
        self.parsers = self.get_parse(parse_info)
        for parser in self.parsers:
            if vcf_entry.INFO.get(parser['id']):
                print(parser['parse_func'](vcf_entry.INFO.get(parser['id'])))

    def get_parse(self, parse_info):

        def _construct_parser(entry):

            def _type_conv(type_str=None):
                if type_str == 'str':
                    return lambda value: str(value)
                if type_str == 'int':
                    return lambda value: int(value)
                if type_str == 'list':
                    return lambda value: list(value)
                if type_str == 'float':
                    return lambda value: float(value)
                return lambda value: value

            def parser_func(raw_value):
                if entry['multivalue']:
                    info_list = []
                    for raw_value_entry in raw_value.split(entry['separator']):
                        info_dict = {}
                        if entry.get('format_separator'):
                            for target, value in zip(entry['format'].split(entry['format_separator']), raw_value_entry.split(entry['format_separator'])):
                                target = target.strip()
                                if entry['target'] == 'all' or target in entry['target']:
                                    info_dict[target] = value
                        info_list.append(info_dict)
                    return _type_conv(entry.get('out_type'))(info_list)
                else:
                    if entry.get('format') and entry.get('format_separator'):
                        for target, value in zip(entry['format'].split(entry['format_separator']), raw_value.split(entry['format_separator'])):
                            target = target.strip()
                            if target in entry['target']:
                                return _type_conv(entry.get('out_type'))(value)
                    else:
                        return _type_conv(entry.get('out_type'))(raw_value)


            return parser_func

        parsers = []
        for entry in parse_info:
            parser = {}
            parser['id'] = entry['id']
            parser['parse_func'] = _construct_parser(entry)
            parsers.append(parser)
        return parsers


    def _find_region(self, padding):
        """
            Given a vcf entry, this function attempts to return the relevant genomic regions
            to where the reads aligned that supports the given variant.

            Args:

                padding (int): given in bp, extends the region for where to look for reads in the
                alignment files.

            Returns:

                vtype (str): variant type
                region (dict): dictionary holding the start and end coordinates for a genomic region

        """

        #For variants with an ID 'SVTYPE' in the INFO field of the vcf entry
        start, end = self._find_start_end()

        vtype = self.entry.INFO.get("TYPE") or self.entry.INFO.get("SVTYPE") or 'None'
        vtype = vtype.upper()

        region = {"start": start - padding,
                  "end": end + padding}

        return vtype, region

    def _find_start_end(self):
        start = self.entry.start
        if self.entry.INFO.get('END'):
            end = self.entry.INFO.get('END')
        else:
            end = self.entry.end
        return (int(start), int(end))


    def _find_genotypes(self):

        """
            Finds genotype calls for each sample, using the GT, DP, GQ, AD fields

        """

        samples = {}
        for i in range(len(self.samples)):

            sample_id = self.samples[i]

            #IDs from sample specific genotype field
            sample = {

                'GT': resolve_cyvcf2_genotype(self.entry.genotypes[i]),
                'DP': int(self.entry.gt_depths[i]),
                'GQ': int(self.entry.gt_quals[i]),
                'AD': int(self.entry.gt_alt_depths[i])

            }

            samples[sample_id] = sample

        return samples

    def _find_genes(self):

        genes = self.entry.INFO.get('ANN')
        if genes is None:
            LOG.debug("Could not find ANN field in vcf")
            return []

        gene_list = []
        for gene in genes.split(','):
            gene_info = {}
            for ann_id, info in zip(GENE_INFO, gene.split('|')):
                gene_info[ann_id] = info.strip() if info else 'unknown'
            gene_list.append(gene_info)

        return gene_list


    def build_variant_object(self, padding, rank_model_version=None):
        """
            makes a dictionary of the variant to be loaded into a mongodb
        """

        #Find genotype and sample id for the samples given in the vcf file
        vtype, region = self._find_region(padding)
        samples = self._find_genotypes()
        genes = self._find_genes()

        self['display_name'] = self.display_name
        self['variant_type'] = vtype
        self['alt'] = self.entry.ALT
        self['ref'] = self.entry.REF
        self['chrom'] = self.entry.CHROM
        self['start'] = self.entry.start
        self['end'] = self.entry.end
        self['vcf_entry'] = str(self.entry)
        self['reads_region'] = region
        self['samples'] = samples
        self['padding'] = padding
        self['genes'] = genes

        #Add data from the info INFO field
        for info_id in INFO_IDS:
            if self.entry.INFO.get(info_id):
                self[info_id] = self.entry.INFO[info_id]

        #Add rank_model_version if given
        if rank_model_version is not None:
            self['rank_model_version'] = rank_model_version

    @property
    def display_name(self):

        """
            Make display name <chrom>_<pos>_<ref>_<alt>
        """

        display_name = '_'.join(
            [
                self.entry.CHROM,
                str(self.entry.POS),
                self.entry.REF,
                self.entry.ALT[0]
            ]
        )

        return display_name



def resolve_cyvcf2_genotype(cyvcf2_gt):
    """
        Given a genotype given by cyvcf2, translate this to a valid
        genotype string.

        Args:
            cyvcf2_gt (cyvcf2.variant.genotypes)

        Returns:
            genotype (str)
    """

    if cyvcf2_gt[2]:
        separator = '|'
    else:
        separator = '/'
    if cyvcf2_gt[0] == -1:
        a_1 = '.'
    else:
        a_1 = str(cyvcf2_gt[0])
    if cyvcf2_gt[1] == -1:
        a_2 = '.'
    else:
        a_2 = str(cyvcf2_gt[1])
    genotype = a_1 + separator + a_2

    return genotype


def get_variants(vcf_file, padding, rank_model_version=None):

    """

        Given a vcf file, this function parses through the file and yields the variant with all
        relevant information

        Args:
            vcf_file (string): Path to vcf file

        Yields:
            variant (mutacc.builds.build_variant.Variant): Variant object
    """

    vcf_file = parse_path(vcf_file)
    vcf = VCF(str(vcf_file), 'r')
    samples = vcf.samples
    for entry in vcf:
        yield Variant(entry, samples, padding, parse_info={}, rank_model_version=rank_model_version)
    vcf.close()

if __name__ == '__main__':
    import yaml
    vcf_file = '/Users/adam.rosenbaum/mutacc_validation/mip7/test_set_gatkcomb_rhocall_vt_frqf_cadd_vep_parsed_snpeff_ranked.selected.vcf.gz'
    vcf = VCF(vcf_file)
    samples = vcf.samples
    count = 0
    with open('/Users/adam.rosenbaum/develop/mutacc/mutacc/resources/vcf-info-def.yaml') as handle:
        parse_info = yaml.load(handle)
    for entry in vcf:
        variant = Variant(entry, samples, 300, parse_info=parse_info)

        count += 1
        if count == 10:
            break
