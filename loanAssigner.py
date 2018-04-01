#!/usr/bin/python

#########################################
#########################################
# Intro: this program is written for the loan assignment take home project for Affirm
#
# Input (4 files) : facilities.csv, banks.csv, loans.csv, covenants.csv
# Output (2 files) : assignments.csv, yields.csv
#
# Process Flow : 
#   1) Populate data model from Input > 
#   2) Pre-process Input by sorting facilities by cost > 
#   3) Stream process each loan >
#       a) for each loan, check facilities in ascending cost order
#       b) checkYield(), checkAmount(), checkRisk(), checkState()
#       c) assign loan to first passing facility, update data model
#   4) Generate Output Files
#
#########################################


#########################################
# Import stuff
#########################################
import csv
import math
import time

start = time.time()

#########################################
# Data model
# define objects for: facility, bank(currently not utilized), covenant, loan
#########################################

# hashMaps for processing
banks = {}
facilities = {}
loans = {}
covenantsG = {}     # general covenants are indexed by bankID
covenantsS = {}     # specific covenants are indexed by facilityID

# for generating output
assignment = []
yields = []

class facility:
    def __init__(self, var1, var2, var3, var4):
        self.id = var1
        self.bankID = var2
        self.amount = var3
        self.remaining = var3
        self.rate= var4
        # store loans assigned to this facility
        self.loans = []
        # for making yields.csv later
        self.expectedYield = 0

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
# Read Input
# read facilities.csv, banks.csv (currently not utilized), and covenants.csv, populating objects' hashMaps
# this section is input file format specific
#########################################

with open('banks.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        bankID = int(row[0])
        name = row[1]
        # add to object hashMap
        banks[bankID] = bank(bankID, name)
f.close()

with open('facilities.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        facilityID = int(row[2])
        bankID = int(row[3])
        # add to object hashMap
        facilities[facilityID] = facility(facilityID, bankID, float(row[0]), float(row[1]))
f.close()

with open('covenants.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        bankID = int(row[2])

        if row[0] == '':
            facilityID = None
        else:
            facilityID = int(row[0])

        if row[1] == '':
            defaultTolerance = float('inf')
        else:
            defaultTolerance = float(row[1])

        banState = row[3].strip()

        # covenants that don't apply to specific facilityID apply to all facilities of the respective bank
        if not facilityID:
            general = True
        else:
            general = False

        # add to object hashMap
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
f.close()


#########################################
# Pre-process Input
# there is no guarantee that cheaper facilities have smaller IDs, so we need to sort them
# make an array where facility IDs are sorted in ascending order in terms of cost
#########################################

# construct index and cost pairs
facilityCostPairs = []
for i in facilities:
    facilityCostPairs.append((facilities[i].id, facilities[i].rate))

# sort pairs by cost
facilitiesSorted = sorted(facilityCostPairs, key=lambda i: i[1])
# drop cost and convert tuple to list
facilitiesSorted = list( zip(*facilitiesSorted)[0] )


#########################################
# Define loan validity checks 
# define functions checkYield(), checkAmount(), checkRisk(), checkState()
#########################################

def checkYield (defaultChance, loanRate, amount, costRate):
    # returns yield amount
    loanYield = (1-defaultChance) * loanRate * amount - defaultChance* amount - costRate * amount
    return loanYield

def checkAmount (loanAmount, facilityRemaining):
    # returns bool
    if facilityRemaining - loanAmount >= 0:
        return True
    else:
        return False

def checkRisk (risk, tolerance):
    # returns bool
    if tolerance >= risk:
        return True
    else:
        return False

def checkState (state, banned):
    # returns bool
    if state.strip() in banned:
        return False
    else:
        return True


#########################################
# Process Loans
#########################################

def assignLoan (loanID, facilityID, yieldAmount):
    facilities[facilityID].loans.append(loanID)
    facilities[facilityID].remaining -= loans[loanID].amount
    facilities[facilityID].expectedYield += yieldAmount
    loans[loanID].facilityID = facilityID

with open('loans.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        loanID = int(row[2])
        state = row[4]
        amount = float(row[1])
        rate = float(row[0])
        defaultChance = float(row[3])
        # add to object hashMap
        loans[loanID] = loan(loanID, state, amount, rate, defaultChance)

        # identify cheapest valid facility
        for i in facilitiesSorted:

            try:
                # round down to 2 decimals
                yieldAmount = int(round(checkYield(defaultChance, rate, amount, facilities[i].rate)))
                if yieldAmount < 0:
                    raise Exception()
                if not checkAmount(amount, facilities[i].remaining):
                    raise Exception()

                # check facility specific covenants 
                for j in range (len(covenantsS[i])):
                    cov = covenantsS[i][j]
                    if not checkRisk(defaultChance, cov.defaultTolerance):
                        raise Exception()
                    if not checkState(state, cov.banState):
                        raise Exception()

                # check bank's general covenants
                checkBank = facilities[i].bankID

                if checkBank in covenantsG :
                    for j in range (len(covenantsG[checkBank])):
                        cov = covenantsG[checkBank][j]
                        if not checkRisk(defaultChance, cov.defaultTolerance):
                            raise Exception()
                        if not checkState(state, cov.banState):
                            raise Exception()

                # if all checks passed, assign loan
                assignLoan(loanID, i, yieldAmount)
                break

            except Exception:
                if i == facilitiesSorted[-1]:
                    print('no facility match found for: %d') % loanID
                continue

#########################################
# Generate output
#########################################

with open('assignments.csv', 'w') as f1:
    fieldNames = ['loan_id', 'facility_id']
    writer = csv.DictWriter(f1, fieldnames = fieldNames)
    writer.writeheader()
    for i in loans:
        writer.writerow({'loan_id': loans[i].id, 'facility_id': loans[i].facilityID})
f1.close()

with open('yields.csv', 'w') as f2:
    fieldNames = ['facility_id', 'expected_yield']
    writer = csv.DictWriter(f2, fieldnames = fieldNames)
    writer.writeheader()
    for i in facilities:
        writer.writerow({'facility_id': facilities[i].id, 'expected_yield': facilities[i].expectedYield})
f2.close()

end = time.time()
duration = end - start
print ('assignment finished, total runtime: %5.4f ms') % (duration*1000)
print('assignments.csv and yields.csv have been created')


#########################################
# Tests
#########################################

# print('False: ', checkAmount (160,150))
# print('True: ', checkAmount (150,150))
# print('True: ', checkAmount (149,150.00))