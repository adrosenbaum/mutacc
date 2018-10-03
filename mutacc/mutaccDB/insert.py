import pymongo

def insert_entire_case(mutacc_adapter, case):
    """
        Insert an entire case into mongodb database. That is, case, samples, and variants.

        Args:
            mutacc_adapter(mutacc.mutaccDB.db_client.MutaccAdapter): Adapter instantiated with a
            client to mongodb instance and db name. 
            
            case(mutacc.builds.build_case.CompleteCase): Instance of class CompleteCase containing
            information about the case, variants, and samples in the case.

    """
    #Save case_id and Sample_ids of the case
    case_id = case.case_id
    sample_ids = case.sample_ids

    #Check if case_id already exists in collection 'cases'    
    if mutacc_adapter.case_exists(case_id):
        
        raise pymongo.errors.WriteError("Case %s already exists" % (case_id)) 
    
    #Check if any sample_id already exist in collection 'samples'
    for sample_id in sample_ids:

        if mutacc_adapter.sample_exists(sample_id):

            raise pymongo.errors.WriteError("Sample %s already exists" % (sample_id))
    
    #Store variants-, samples-, and case objects as variants, samples, and cases. 
    variants = case.variants_object
    samples = case.samples_object
    case = case.case_object
    
    #add case_id and sample_ids fields for variant objects, pointing to the case, and samples where
    #the variants come from
    for variant in variants:

        variant["case"] = case_id
        variant["samples"] = sample_ids

    #Insert variants into db and save ObjectIds for the documents as variant_ids
    variant_ids = mutacc_adapter.add_variants(variants)    
    
    #Add variant_ids and case_id to sample objects
    for sample in samples:

        sample["variants"] = variant_ids
        sample["case"] = case_id
    
    #Insert sample objects into db
    mutacc_adapter.add_samples(samples)

    #Add variant_ids and sample_ids to case object
    case["variants"] = variant_ids
    case["samples"] = sample_ids
    
    #Insert case into db
    mutacc_adapter.add_case(case)
