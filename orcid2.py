"""
ORCID 2.0 but without having to download the data, just on the fly
For each provided orcid it returns:
- ORCID: the provided ORCIDs as identifier.
- The number of potential papers: papers that share the name of the author of interest and could possibly be from him/her.
- The number of linked papers: the number of papers from the potential that were already linked by the author's ORCID, so they aren't new.
- The number of new found papers: the number of papers that the algorithm thinks are from the author but were not linked by their ORCID.
- New found papers: the PMIDs of the different newly found papers.
* If verbose, also returns:
- For each iteration, the papers that were retrieved using collaborators ORCIDs. 
  If there are no more papers that can be linked trought colalborators ORCIDs, then it returns the results of applying the score system.
"""

import pandas
import numpy
import unicodedata
from operator import itemgetter
import requests
import json
import pickle

def remove_accents_and_lower(name, aslist = True):
    """Was used in the previous version. Should be used also in this version to reach some pesky papers that have typos or inconsistencies
    in the author's name. But again, this is tricky to use properly and because of the time constraints hasn't been yet incorporated into the code."""
    if aslist:
        names = name
        names = [unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode().lower().replace('-', ' ').replace('.', '') for name in names]
        name = names
    else:
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode().lower().replace('-', ' ').replace('.', '')
        name = name.lower().replace('-', ' ')
    return name

def retrieve_possible_papers_and_ORCIDs(ORCID, verbose = False):
    """Main function to do the queries into the pubmed restful API. """
    search_module = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query='
    format = 'json' #Can be 'json' or 'xml'.
    query = ORCID # The query to make to the database. 
    result_Type = 'core' # It is the ammount of information to retrieve for each match. From less to more: 'idlist','lite', or 'core'. Core contains all what's avaiable.
    cursorMark = '*'
    i = 0
    results = {}
    authors = {}
    papers = {}
    if verbose:
        print('Starting restful GET process from ePMC. This will take time.')
    while True:
        i += 1
        try:
            r = (requests.get(search_module+query+'&format='+format+'&resultType='+result_Type+"&cursorMark="+cursorMark+"&pageSize=1000")).json()
            if verbose:
                print(str(i*1000) + ' papers retrieved')
        except:
            print('Connection broken. Retrieving: ' + str(i*1000) + ' papers. To continue, please start from the folling key ' + cursorMark)
            break
        if len(r['resultList']['result']) > 0:
            for result in r['resultList']['result']:
                try:
                    papers[result['pmid']] = set([])
                    if 'authorList' in result:
                        results[result['pmid']] = {variable:result[variable] for variable in ['title', 'pubYear', 'authorString','authorList']}
                        for author in result['authorList']['author']:
                            if 'authorId' in author:
                                papers[result['pmid']].add(author['authorId']['value'])
                                if author['authorId']['value'] in authors:
                                    authors[author['authorId']['value']]['papers'].add(result['pmid'])
                                else:
                                    authors[author['authorId']['value']] = {variable:author[variable]for variable in ['firstName','lastName', 'fullName'] if variable in author}
                                    authors[author['authorId']['value']]['papers'] = set([result['pmid']])
                    else:
                        results[result['pmid']] = {variable:result[variable] for variable in ['title', 'pubYear', 'authorString']}
                except:
                    pass
            cursorMark = r['nextCursorMark']
        else:
            if verbose:
                print('File limit reached')
            break
    return results, authors, papers

def update_collaborators(collaborators, author,score):
    """Updates the collaborators scores. Which helps to infer the likelihood of a paper being 
    from the author of interest"""
    if author in collaborators:
        collaborators[author] += score
    else:
        collaborators[author] = score
    return collaborators

def compute_initial_collaborations(ORCID, papers):
    """Retrieves the initial collaboration data using the papers that have the author's ORCID linked"""
    collaborations = {}
    collaborations_orcids = set([])
    initial_names = set([])
    for paper in papers:
        for author in papers[paper]['authorList']['author']:
            if 'fullName' in author and 'firstName' in author:
                update_collaborators(collaborations, (author['fullName'],author['firstName']), 20)
            else:
                continue
            if 'authorId' in author:
                if author['authorId']['value'] != ORCID:
                    collaborations_orcids.add(author['authorId']['value'])
                else:
                    initial_names.add((author['fullName'],author['firstName']))
    for name in initial_names:
        del(collaborations[name])
    return collaborations, collaborations_orcids, initial_names

def retrieve_potential_papers(ORCID, authors, initial_papers):
    """Gets all the papers that could potentially belong to the author of interest. It searches for them using the authors family name 
    and first letter name. Like: Darwin C."""
    potential_papers, potential_papers_authors, potential_papers_orcids = retrieve_possible_papers_and_ORCIDs(authors[ORCID]['fullName'])
    for paper in initial_papers:
        if paper in potential_papers:
            del potential_papers[paper]
    return potential_papers, potential_papers_authors, potential_papers_orcids

def verify_in_orcids(potential_papers, collaborations_orcids, ORCID):
    """Check if there is an author in the potential paper that shares an ORCID with one previously 
    found collaborator. If so, it is considered as a new paper. """
    new_found_papers = set([])
    new_collaborators = set([])
    for paper in potential_papers:
        for orcid in potential_papers_orcids[paper]:
            if orcid in collaborations_orcids:
                collaborations_orcids.update(potential_papers_orcids[paper].difference(set([ORCID])))
                new_collaborators.update(potential_papers_orcids[paper].difference(set([ORCID])))
                new_found_papers.add(paper)
    return collaborations_orcids, new_found_papers, new_collaborators

def calculateScoreThreshold(paper, pmid,collaborations, iteration, initial_names, verbose = False):
    scores = []
    exact_name = False
    for author in paper['authorList']['author']:
        if 'firstName' in author and 'fullName' in author:
            if (author['fullName'], author['firstName']) in collaborations:
                scores.append(collaborations[(author['fullName'], author['firstName'])])
            elif (author['fullName'], author['firstName']) in initial_names:
                exact_name = True
            else:
                score = sum([collaborations[colaborator] for colaborator in collaborations if colaborator[0] == author['fullName']])/2
                if score > 0:
                    scores.append(score)
    nonzeros = len(scores)
    score = sum(scores)
    if exact_name:
        score = score * 2
    threshold = len(paper['authorList']['author'])*iteration*len(set([(y['fullName'], y['firstName']) for x in potential_papers for y in potential_papers[x]['authorList']['author'] if  ('fullName' in y) and (y['fullName'].split(' ')[0] in [z[0].split(' ')[0] for z in initial_names]) and ('firstName' in y)]))
    score = score*nonzeros**2
    if verbose:
        print("Paper %s\tScore: %d\tMultiplier: %d\tThreshold: %d" % (pmid,score, nonzeros, threshold))
    if score > threshold:
        return True
    else:
        return False

def verify_by_score(potential_papers, collaborations, iteration,initial_names, ORCID, verbose = False):
    new_found_papers = set([])
    new_collaborators_orcid = set([])
    new_collaborators = set([])
    for paper in potential_papers:
        if calculateScoreThreshold(potential_papers[paper], paper,collaborations, iteration, initial_names, verbose):
            new_found_papers.add(paper)
            new_collaborators_orcid.update(potential_papers_orcids[paper].difference(set([ORCID])))
            new_collaborators.update({(author['fullName'], author['firstName']) for author in potential_papers[paper]['authorList']['author'] if 'fullName' in author and 'firstName' in author})
    return new_found_papers, new_collaborators_orcid, new_collaborators

def search_papers(potential_papers ,papers, authors, potential_papers_authors, collaborations_orcids, collaborations, ORCID, verbose = False):
    new_found_papers = set([])
    new_found_papers_by_orcid = set([])
    iteration = 0
    while True:
        iteration += 1
        if verbose:
            print("Interation: %d" %(iteration))
        collaborations_orcids, new_found_papers_by_orcid, new_collaborators = verify_in_orcids(potential_papers, collaborations_orcids, ORCID)
        if len(new_collaborators) > 0:
            for collaborator in new_collaborators:
                collaborations = update_collaborators(collaborations, (potential_papers_authors[collaborator]['fullName'], potential_papers_authors[collaborator]['firstName']), 20)
            new_collaborators = set([])
        if len(new_found_papers_by_orcid) > 0:
            new_found_papers.update(new_found_papers_by_orcid)
            for paper in new_found_papers_by_orcid:
                del potential_papers[paper]
            if verbose:
                print(len(new_found_papers_by_orcid), ' new found papers by collaborators ORCIDs')
            new_found_papers_by_orcid = set([])
            continue
        else:
            new_found_papers_by_score, new_collaborators_orcid, new_collaborators = verify_by_score(potential_papers, collaborations, iteration, initial_names, ORCID, verbose=verbose)
            if len(new_collaborators_orcid) > 0:
                for collaborator in new_collaborators_orcid:
                    if 'fullName' in potential_papers_authors[collaborator] and 'firstName' in potential_papers_authors[collaborator]:
                        collaborations = update_collaborators(collaborations, (potential_papers_authors[collaborator]['fullName'], potential_papers_authors[collaborator]['firstName']), 20)
                new_collaborators_orcid = set([])
            if len(new_collaborators) > 0:
                for collaborator in new_collaborators:
                    collaborations = update_collaborators(collaborations, (collaborator[0], collaborator[1]), 10)
                new_collaborators = set([])
            new_found_papers.update(new_found_papers_by_score)
            if len(new_found_papers_by_score) > 0:
                for paper in new_found_papers_by_score:
                    del potential_papers[paper]
                if verbose:
                    print(len(new_found_papers_by_score), ' new found papers by score')
                new_found_papers_by_score = set([])
            else:
                if verbose:
                    print('No more papers were found.')
                return new_found_papers

def delete_exisiting_papers(found_papers, papers):
    new_papers = set([])
    for paper in found_papers:
        if paper not in papers:
            new_papers.add(paper)
    return new_papers


if __name__ == '__main__':
    print('Please, enter the ORCIDs from which you want to retrieve the papers. You might enter more than one separated by commas. Add, \'verbose\' at the end for detailed results.')
    ORCIDs = input('')
    ORCIDs = ORCIDs.replace(' ', '')
    ORCIDs = ORCIDs.split(',')
    if ORCIDs[-1].lower() == 'verbose':
        verbose = True
        ORCIDs.remove('verbose')
    else:
        verbose = False
    if type(ORCIDs) == str:
        ORCIDs = [ORCIDs]
    for ORCID in ORCIDs:
        try:
            data, authors, papers= retrieve_possible_papers_and_ORCIDs(ORCID, verbose = verbose)
            collaborations, collaborations_orcids, initial_names = compute_initial_collaborations(ORCID, data)
            potential_papers, potential_papers_authors, potential_papers_orcids = retrieve_potential_papers(ORCID, authors, papers)
            n_potential_papers = len(potential_papers)
            new_found_papers = search_papers(potential_papers, papers, authors, potential_papers_authors, collaborations_orcids, collaborations, ORCID, verbose = verbose)
            new_papers = delete_exisiting_papers(new_found_papers, papers)
            print('ORCID:\t', ORCID, 'Potential Papers:\t',n_potential_papers,', Linked Papers:\t', len(papers),', New found papers:\t', len(new_papers), new_papers)
        except:
            print('Something went wrong. Probably and in invalid ORCID: ', ORCID)