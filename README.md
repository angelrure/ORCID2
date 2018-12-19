# ORCID2

This is a script uses the pubmed API and a scoring function to retrieve papers that authors forgot to link to their ORCID. 

----------------------------
# Table of Contents
----------------------------

   * [Overview](#overview)
   * [Installation](#installation)
   * [Commands and options](#commands-and-options)
   * [Inputs and Outputs](#inputs-and-outputs)
   * [Usage example](#usage-example)
   
----------------------------
# Overview
----------------------------

ORCID2 requieres internet connection to access the Pubmed RESTful API to retrieve papers that authors did not link to their ORCID. It does so by using a scoring function that takes into consideration the colaborators of the author, the number of time they collaborate and the frequency of the names, both from the authors and from the collaborators.

----------------------------
# Installation
----------------------------

ORCID2 doesn't need instalation. Just clone the repository and run it like a normal script. 
(Installation via pip will be added soon)

----------------------------
# Inputs and Outputs
----------------------------

Once the program is started, the user must enter a list of ORCIDs separated by commas and the word 'verbose' if the users wishes to see the scoring function values for the papers. 

The output of the program consists of the ORCID, the potential papers (papers that contain the author name and are not linked), the already linked papers and the pmids of the new found papers. See the example below.

----------------------------
# Usage example
----------------------------

After starting the script, if the user enters the following two ORCIDs like this:

```
0000-0001-6201-5599, 0000-0003-0793-6218
```
it returns:
```
ORCID:	 0000-0001-6201-5599 Potential Papers:	 4 , Linked Papers:	 79 , New found papers:	 4 {'29563166', '29452591', '29958939', '29860520'}
ORCID:	 0000-0003-0793-6218 Potential Papers:	 13 , Linked Papers:	 62 , New found papers:	 13 {'27513819', '28298237', '28903032', '29617666', '30181341', '27365209', '28854369', '27857118', '29596423', '29155959', '29592900', '28005460', '27763814'}


