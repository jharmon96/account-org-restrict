from jackLib.stanfun import init_brwsr, login
import sys
import csv
import os
import selenium

# Enter parameters for customer site
URL = 'http://sites.unanet.com/demo_jharmon/action'
username = 'fcontroller'
password = 'welcome'
import_file = './import-files/account-org-restrict.csv'
account_ref_file = ''

class AccountProfile:
    key = 0
    name = 0
    orgs = 0

def mkRefFile(tbody, ref_file, clmPadding):

    """ Creates csv from Unanet table
        Fields:
            tbody - html table
            ref_file - save file name
            clmPadding - column padding in case headers don't line up to values
    """

    head = tbody.find_element_by_tag_name('thead')
    body = tbody.find_element_by_tag_name('tbody')

    file_data = []

    head_line = head.find_element_by_tag_name("tr")
    file_header = [header.text for header in head_line.find_elements_by_tag_name('td')]
    for x in range(clmPadding):
        file_header.insert(0, '')
    file_header.insert(0,'key')
    file_data.append(",".join(file_header))

    body_rows = body.find_elements_by_tag_name('tr')
    for row in body_rows:
        data = row.find_elements_by_tag_name('td')
        key = row.get_attribute("id").strip("k_").strip("r")
        file_row = []
        for datum in data:
            datum_text = datum.text
            file_row.append(datum_text)
            print(datum_text)
        file_row.insert(0, key)
        file_data.append(",".join(file_row))

    with open(ref_file, "w") as f:
        f.write("\n".join(file_data))

    # open import file and assign local values. Match up to account-ref csv and take action.
def compFiles(import_file, account_ref_file):
    """Takes import and account ref files and matches orgs to accounts"""

    acctOrgs = {}
    authOrgKeys = ''
    total = 0
    import_file = csv.DictReader(open(import_file, newline='', encoding="utf-8-sig"))
    for row in import_file:
        account_code = str(row["account_code"])
        auth_orgs = str(row["auth_orgs"])

        account_ref = csv.DictReader(open(account_ref_file, newline='', encoding="utf-8-sig"))
        for account in account_ref:
            account_code_ref = str(account["ACCOUNT"])
            #auth_orgs_ref = str(account["auth_orgs"])
            acct_key_ref = str(account["key"])

            if account_code_ref.startswith(account_code):
                total = total + 1

                # takes org name from import file and turns it into the DB key

                orgnames = auth_orgs.split(",")
                for orgname in orgnames:
                    print('orgname: ' + orgname)
                    org_file = csv.DictReader(open('./tmp/org-ref.csv', newline='', encoding="utf-8-sig"))
                    for org in org_file:
                        if orgname == str(org["ORG CODE"]):
                            authOrgKey = str(org["key"])
                    authOrgKeys = authOrgKeys + authOrgKey + ','
                    #authOrgKeys = authOrgKeys[1:]
                    acctOrgs.update({acct_key_ref : authOrgKeys})
                authOrgKeys = ''
    print(acctOrgs)
    return acctOrgs
        #print(str(total) + ' total matches for accounts starting with ' + account_code)


def getTable(driver, urlSuffix, search):
    """Goes to a list page and returns the table"""

    # Navigate to accounts list on admin > setup
    driver.get(URL + urlSuffix)

    if search:
        xpath = '//*[@id="tab.list.search"]/div/form/table/tbody/tr[1]/td[1]/table/tbody/tr[1]/td[2]/input'
        driver.find_element_by_xpath(xpath).send_keys('10.06')
        xpath = '//*[@id="account_fltr"]'
        driver.find_element_by_xpath(xpath).click()

    xpath = '//*[@id="tab.list.list_head"]'
    driver.find_element_by_xpath(xpath).click()

    # capture table of accoutns
    xpath = '//*[@id="tab.list.list"]'
    tbody = driver.find_element_by_xpath(xpath)
    return tbody

def goToAcctOrgs(driver, key):
    # Open account profile > click on Organizations > Ex
    driver.get(URL + '/admin/setup/accounting/account/edit?key=' + str(key))
    xpath = '//*[@id="tab.account.organizations_head"]'

    driver.find_element_by_xpath(xpath).click()

    xpath = '//*[@id="orgaccess-specified"]'
    driver.find_element_by_xpath(xpath).click()

    xpath = '//*[@id="tree-pane"]'
    imgs = driver.find_element_by_xpath(xpath).find_elements_by_tag_name('img')
    imgs[0].click()

def restrictOrgs(driver, authOrgs):
    """Takes in a list of accounts and their authorized orgs then click check boxes to restrict"""

    for key, value in authOrgs.items():
        goToAcctOrgs(driver, key)
        xpath = '//*[@id="tree-data"]'
        inputTable = driver.find_element_by_xpath(xpath)
        inputs = inputTable.find_elements_by_tag_name('input')
        # print(inputs)
        orgKeys = value.split(",")
        orgKeys.pop()
        print('Account Key: ' + key)
        for input in inputs:
            if input.find_element_by_xpath('..').get_attribute('class') == 'chosen':
                input.click()
        for orgKey in orgKeys:
            print ('Org Key: ' + orgKey)
            for input in inputs:
                inputKey = input.get_attribute('value')
                if inputKey == orgKey:
                    input.click()

        xpath = '//*[@id="button_save"]'
        driver.find_element_by_xpath(xpath).click()

        #xpath = '//*[@id="button_cancel"]'
        #driver.find_element_by_xpath(xpath).click()

class credentials:
    def __init__(self):
        pass

    def prompt(self, url, username, password, skipRemap):
        self.url = input("What is the URL? \nExample: 'http://sites.unanet.com/demo'\n")
        self.username = input("Enter the username: ")
        self.password = input("Enter the password: ")
        self.skipRemap = input("Skip Org & Account Mapping? (Y/N) ")


if __name__ == "__main__":

    # cr = credentials()
    # cr.prompt('url', 'username', 'password', 'skipRemap')

    # Initialize driver and login to Unanet
    driver = init_brwsr(False,'./tmp')
    # login(driver, cr.url, cr.username, cr.password)
    login(driver, URL, username, password)

    skipRemap = "N"
    if skipRemap == "N":
    # if cr.skipRemap == "N":
        try:
           os.remove(r'./tmp/account-ref.csv')
           os.remove(r'./tmp/org-ref.csv')
        except:
           pass

        tbody = getTable(driver, '/admin/setup/accounting/account/list', False)
        mkRefFile(tbody, './tmp/account-ref.csv', 1)

        tbody = getTable(driver, '/organizations/list', False)
        mkRefFile(tbody, './tmp/org-ref.csv', 3)

    authOrgs = compFiles(import_file, './tmp/account-ref.csv')

    restrictOrgs(driver, authOrgs)
