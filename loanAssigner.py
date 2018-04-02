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
#       b) check_yield(), check_amount(), check_risk(), check_state()
#       c) assign loan to first passing facility, update data model, generate Output
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
# Data model & Functions
# define objects for: Facility, Covenant
# define functions check_yield(), check_amount(), check_risk(), check_state(), assign_loan(), call_all_checks()
#########################################

class LoanProcessor:
    facilities = {}         # indexed by facilityID
    covenantsG = {}         # general covenants are indexed by bankID
    covenantsS = {}         # specific covenants are indexed by facilityID
    assignment = []         # for generating output
    yields = []             # for generating output
    facilityCostPairs = []  # construct index and cost pairs
    facilitiesSorted = []   # facilities' indexes in cost ascending order

    def check_yield (self, defaultChance, loanRate, amount, costRate):
        # returns yield amount
        loanYield = (1-defaultChance) * loanRate * amount - defaultChance* amount - costRate * amount
        return loanYield

    def check_amount (self, loanAmount, facilityRemaining):
        # returns bool
        if facilityRemaining - loanAmount >= 0:
            return True
        else:
            return False

    def check_risk (self, risk, tolerance):
        # returns bool
        if tolerance >= risk:
            return True
        else:
            return False

    def check_state (self, state, banned):
        # returns bool
        if state.strip() in banned:
            return False
        else:
            return True
    
    def call_all_checks (self, defaultChance, rate, amount, i, state):
        # call all loan assignment validity checks, returns bool

        # round down to 2 decimals
        yieldAmount = int(round(self.check_yield(defaultChance, rate, amount, self.facilities[i].rate)))
        if yieldAmount < 0:
            return False
        if not self.check_amount(amount, self.facilities[i].remaining):
            return False

        # check facility specific covenants
        if i in self.covenantsS:
            for j in range (len(self.covenantsS[i])):
                cov = self.covenantsS[i][j]
                if not self.check_risk(defaultChance, cov.defaultTolerance):
                    return False
                if not self.check_state(state, cov.banState):
                    return False

        # check bank's general covenants
        checkBank = self.facilities[i].bankID
        if checkBank in self.covenantsG :
            for j in range (len(self.covenantsG[checkBank])):
                cov = self.covenantsG[checkBank][j]
                if not self.check_risk(defaultChance, cov.defaultTolerance):
                    return False
                if not self.check_state(state, cov.banState):
                    return False
        return True

    def assign_loan (self, loanID, facilityID, yieldAmount, amount):
        self.facilities[facilityID].loans.append(loanID)
        self.facilities[facilityID].remaining -= amount
        self.facilities[facilityID].expectedYield += yieldAmount
        # in production code, it is a good idea to save this info to loan object
        # self.loans[loanID].facilityID = facilityID

class Facility:
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

class Covenant:
    # covenants are stored either covenantsG (general) or covenantsS (specific)
    def __init__(self, var1, var2, var3, var4, var5):
        self.bankID = var1
        self.facilityID = var2
        self.defaultTolerance = var3
        self.banState = var4
        self.general = var5

#########################################
# Read Input
# read facilities.csv, and covenants.csv, populating objects' hashMaps
# this section is input file format specific
#########################################

with open('facilities.csv','r') as f:
    reader = csv.reader(f)
    # skip column headers
    next(reader, None)
    for row in reader:
        facilityID = int(row[2])
        bankID = int(row[3])
        # add to object hashMap
        LoanProcessor.facilities[facilityID] = Facility(facilityID, bankID, float(row[0]), float(row[1]))
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
        newCovenant = Covenant(bankID, facilityID, defaultTolerance, banState, general)
        if general:
            if bankID in LoanProcessor.covenantsG:
                LoanProcessor.covenantsG[bankID].append(newCovenant)
            else:
                LoanProcessor.covenantsG[bankID] = [newCovenant]
        else:
            if facilityID in LoanProcessor.covenantsS:
                LoanProcessor.covenantsS[facilityID].append(newCovenant)
            else:
                LoanProcessor.covenantsS[facilityID] = [newCovenant]
f.close()


#########################################
# Pre-process Input
# there is no guarantee that cheaper facilities have smaller IDs, so we need to sort them
# make an array where facility IDs are sorted in ascending order in terms of cost
#########################################

for i in LoanProcessor.facilities:
    LoanProcessor.facilityCostPairs.append((LoanProcessor.facilities[i].id, LoanProcessor.facilities[i].rate))

# sort pairs by cost
LoanProcessor.facilitiesSorted = sorted(LoanProcessor.facilityCostPairs, key=lambda i: i[1])

# drop cost and convert tuple to list
LoanProcessor.facilitiesSorted = list( zip(*LoanProcessor.facilitiesSorted)[0] )


#########################################
# Process Loans & Generate Output
#########################################

with open('assignments.csv', 'w') as f1:
    fieldNames = ['loan_id', 'facility_id']
    writer = csv.DictWriter(f1, fieldnames = fieldNames)
    writer.writeheader()

    with open('loans.csv','r') as f2:
        reader = csv.reader(f2)
        # skip column headers
        next(reader, None)
        for row in reader:
            loanID = int(row[2])
            state = row[4]
            amount = float(row[1])
            rate = float(row[0])
            defaultChance = float(row[3])
            # in production code, we would want to add to object hashMap
            # LoanProcessor.loans[loanID] = Loan(loanID, state, amount, rate, defaultChance)

            # identify cheapest valid facility
            # this for-loop can be optimized to start with the first facility that is not filled (remaining available amount < X)
            for i in LoanProcessor.facilitiesSorted:
                processor = LoanProcessor()

                # call all loan assignment validity checks
                if not processor.call_all_checks(defaultChance, rate, amount, i, state):
                    if i == LoanProcessor.facilitiesSorted[-1]:
                        print('no facility match found for: %d') % loanID
                        writer.writerow({'loan_id': loanID, 'facility_id': None})
                    continue
                else:
                    # if all checks passed, assign loan
                    yieldAmount = int(round(processor.check_yield(defaultChance, rate, amount, LoanProcessor.facilities[i].rate)))
                    processor.assign_loan(loanID, i, yieldAmount, amount)
                    writer.writerow({'loan_id': loanID, 'facility_id': i})
                    break
    f2.close()
f1.close()

with open('yields.csv', 'w') as f:
    fieldNames = ['facility_id', 'expected_yield']
    writer = csv.DictWriter(f, fieldnames = fieldNames)
    writer.writeheader()
    for i in LoanProcessor.facilities:
        writer.writerow({'facility_id': LoanProcessor.facilities[i].id, 'expected_yield': LoanProcessor.facilities[i].expectedYield})
f.close()

end = time.time()
duration = end - start
print('assignment finished, total runtime: %5.4f ms') % (duration*1000)
print('assignments.csv and yields.csv have been created')
