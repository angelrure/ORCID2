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
