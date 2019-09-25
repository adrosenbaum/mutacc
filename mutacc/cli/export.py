"""
    Command to export variants
"""
import logging
import json

import click

from mutacc.parse.path_parse import make_dir
from mutacc.mutaccDB.query import mutacc_query
from mutacc.utils.vcf_writer import vcf_writer
from mutacc.utils.sort_variants import sort_variants

LOG = logging.getLogger(__name__)

@click.command()
@click.option('-c', '--case-mongo')
@click.option('-v', '--variant-mongo')
@click.option('-t', '--variant-type')
@click.option('-a', '--analysis', type=click.Choice(['wes', 'wgs']))
@click.option('--all-variants', is_flag=True)
@click.option('-m', '--member',
              type=click.Choice(['father', 'mother', 'child', 'affected']),
              default='affected')
@click.option('-s', '--sex',
              type=click.Choice(['male', 'female']))
@click.option('--vcf-dir', type=click.Path(exists=True))
@click.option('-p', '--proband', is_flag=True)
@click.option('-n', '--sample-name')
@click.option('-j', '--json-out', is_flag=True)
@click.pass_context
def export(context,
           case_mongo,
           variant_mongo,
           variant_type,
           analysis,
           all_variants,
           member,
           sex,
           vcf_dir,
           proband,
           sample_name,
           json_out):

    """
        exports dataset from DB
    """

    #Get mongo adapter from context
    adapter = context.obj['adapter']

    variant_query=None
    case_query=None
    if all_variants:
        variant_query = {}
    else:
        if variant_mongo is not None:
            variant_query=json.loads(variant_mongo)
        if case_mongo is not None:
            case_query=json.loads(case_mongo)
        if variant_type is not None:
            if variant_query is None:
                variant_query = {'variant_type': variant_type}
            else:
                variant_query['variant_type'] = variant_type
        if analysis:
            if case_query is None:
                case_query = {'samples.0.analysis_type': analysis}
            else:
                case_query['samples.0.analysis_type'] = analysis

    #Query the cases in mutaccDB
    samples, regions, variants = mutacc_query(
        adapter,
        case_query,
        variant_query,
        sex=sex,
        member=member,
        proband=proband
    )

    sample_name = sample_name or member

    #Info to be dumped into file for later use with 'synthesize' command
    query = (samples, regions, variants, sample_name)

    query_dir = context.obj.get('query_dir')

    #json query and dump to file for later use with 'synthesize' command
    json_file = query_dir.joinpath(sample_name + "_query_mutacc.json")

    with open(json_file, "w") as json_handle:

        json.dump(query, json_handle)

    log_msg = f"Query stored in {json_file}"
    LOG.info(log_msg)

    #sort variants
    found_variants = sort_variants(variants)

    #WRITE VCF FILE
    vcf_dir = vcf_dir or context.obj.get('vcf_dir')
    vcf_dir = make_dir(vcf_dir)
    vcf_file = vcf_dir.joinpath("{}_variants.vcf".format(sample_name))

    log_msg = f"creating vcf file {vcf_file}"
    LOG.info(log_msg)

    vcf_writer(found_variants, vcf_file, sample_name)

    if json_out:
        output_info = {'query_file': str(json_file), 'vcf_file': str(vcf_file)}
        output_json = json.dumps(output_info)
        click.echo(output_json)
