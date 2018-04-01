#!/usr/bin/python

#########################################
# Input (4 files): facilities.csv, banks.csv, loans.csv, covenants.csv
# Output (2 files): assignments.csv, yields.csv
#########################################

import csv

#########################################
# define objects for: facility, bank, covenant, loan
#########################################
class facility:
    def __init__(self, var1, var2, var3, var4):
        self.id = var1
        self.bankID = var2
        self.amount = var3
        self.remaining = var3
        self.rate= var4
        # store loans assigned to this facility
        self.loans = []

class covenant:
    # covenants are stored either covenantsG (general) or covenantsS (specific)
    def __init__(self, var1, var2, var3, var4, var5):
        self.bankID = var1
        self.facilityID = var2
        self.defaultTolerance = var3
        self.banState = var4
        self.general = var5

class bank:
    def __init__(self, var1, var2):
        self.id = var1
        self.name = var2

class loan:
    def __init__(self, var1, var2, var3, var4, var5):
        self.id = var1
        self.state = var2
        self.amount = var3
        self.rate = var4
        self.defaultChance = var5
        self.facilityID = None


#########################################
# read facilities.csv, banks.csv, and covenants.csv, populating objects' hashMaps
# this section is input file format specific
#########################################

banks = {}
facilities = {}
# general covenants are indexed by bankID
covenantsG = {}
# specific covenants are indexed by facilityID
covenantsS = {}

loans = {}

with open('banks.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        bankID = int(row[0])
        name = row[1]
        banks[bankID] = bank(bankID, name)

with open('facilities.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        facilityID = int(row[2])
        bankID = int(row[3])
        facilities[facilityID] = facility(facilityID, bankID, float(row[0]), float(row[1]))

with open('covenants.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        bankID = int(row[2])
        facilityID = int(row[0])
        if row[1]:
            defaultTolerance = float(row[1])
        else:
            defaultTolerance = 0
        banState = row[3]

        # covenants that don't apply to specific facilityID apply to all facilities of the respective bank
        if not facilityID:
            general = True
        else:
            general = False

        # add each covenant to respective bank's object
        newCovenant = covenant(bankID, facilityID, defaultTolerance, banState, general)
        
        if general:
            if bankID in covenantsG:
                covenantsG[bankID].append(newCovenant)
            else:
                covenantsG[bankID] = [newCovenant]
        else:
            if facilityID in covenantsS:
                covenantsS[facilityID].append(newCovenant)
            else:
                covenantsS[facilityID] = [newCovenant]

print(covenantsS)
