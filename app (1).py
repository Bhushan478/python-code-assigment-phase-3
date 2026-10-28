"""Advanced Employee Payroll & Tax Management System - Phase III (Streamlit)
Bhushan Marbate [CM25074] | Python Programming Language (N-PCCCM304P)
Run locally:  streamlit run app.py
"""
import json
import re

import pandas as pd
import streamlit as st

DATA_FILE = "employees.json"
TAX_SLABS = [(25000, 0.00), (50000, 0.05), (100000, 0.10), (float("inf"), 0.20)]
PF_RATE = 0.12
PROF_TAX = 200
PROF_TAX_LIMIT = 15000
DEMO = {
    "EMP1001": {"name": "Rahul Sharma", "basic": 30000.0, "allowances": 8000.0, "performance": 80.0},
    "EMP1002": {"name": "Priya Deshmukh", "basic": 40000.0, "allowances": 9000.0, "performance": 92.0},
    "EMP1003": {"name": "Aman Verma", "basic": 26000.0, "allowances": 5000.0, "performance": 65.0},
}


class PayrollError(Exception):
    """Raised for invalid payroll input."""


def calculate_tax(gross):
    tax, previous_limit = 0.0, 0
    for limit, rate in TAX_SLABS:
        amount = min(gross, limit) - previous_limit
        if amount > 0:
            tax += amount * rate
        if gross <= limit:
            break
        previous_limit = limit
    return round(tax, 2)


def calculate_bonus(basic, performance):
    if performance >= 90:
        return basic * 0.15
    if performance >= 75:
        return basic * 0.10
    if performance >= 60:
        return basic * 0.05
    return 0.0


def calculate_salary(emp):
    basic, allowances = emp["basic"], emp["allowances"]
    bonus = calculate_bonus(basic, emp["performance"])
    gross = basic + allowances + bonus
    pf = basic * PF_RATE
    prof_tax = PROF_TAX if gross > PROF_TAX_LIMIT else 0
    income_tax = calculate_tax(gross)
    total = pf + prof_tax + income_tax
    return {"bonus": bonus, "gross": gross, "pf": pf, "prof_tax": prof_tax,
            "income_tax": income_tax, "deductions": total, "net": gross - total}


def validate(emp_id, name, basic, allowances, performance, existing, editing=False):
    emp_id = str(emp_id).strip().upper()
    name = str(name).strip()
    if not re.fullmatch(r"EMP\d{3,6}", emp_id):
        raise PayrollError("Employee ID must look like EMP1001.")
    if not editing and emp_id in existing:
        raise PayrollError(f"Employee ID {emp_id} already exists.")
    if len(name) < 2 or not re.fullmatch(r"[A-Za-z .'-]+", name):
        raise PayrollError("Enter a valid name (letters only).")
    try:
        basic, allowances, performance = float(basic), float(allowances), float(performance)
    except (TypeError, ValueError):
        raise PayrollError("Salary fields must be numbers.")
    if basic <= 0:
        raise PayrollError("Basic salary must be greater than 0.")
    if allowances < 0:
        raise PayrollError("Allowances cannot be negative.")
    if not 0 <= performance <= 100:
        raise PayrollError("Performance must be between 0 and 100.")
    return emp_id, {"name": name, "basic": basic, "allowances": allowances, "performance": performance}


def load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            return data
    except (OSError, ValueError):
        pass
    return json.loads(json.dumps(DEMO))


def save(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        st.warning("Could not save to file; changes last for this session only.")


def inr(v):
    return f"₹{v:,.2f}"


def run_tests():
    cases = []

    def eq(name, a, b):
        cases.append((name, abs(a - b) < 0.005))

    def raises(label, **kw):
        try:
            validate(existing={"EMP1001": 1}, **kw)
            cases.append((label, False))
        except PayrollError:
            cases.append((label, True))

    ok = dict(name="Ann", basic=1, allowances=0, performance=0)
    eq("Tax at 25,000 = 0", calculate_tax(25000), 0)
    eq("Tax at 41,000 = 800", calculate_tax(41000), 800)
    eq("Tax at 55,000 = 1,750", calculate_tax(55000), 1750)
    eq("Tax at 150,000 = 16,250", calculate_tax(150000), 16250)
    eq("Bonus perf 90 = 15%", calculate_bonus(1000, 90), 150)
    eq("Bonus perf 89 = 10%", calculate_bonus(1000, 89), 100)
    eq("Bonus perf 60 = 5%", calculate_bonus(1000, 60), 50)
    eq("Bonus perf 59 = 0", calculate_bonus(1000, 59), 0)
    for k, net in (("EMP1001", 36400), ("EMP1002", 48250), ("EMP1003", 28615)):
        eq(f"{k} net = {net:,}", calculate_salary(DEMO[k])["net"], net)
    raises("Rejects bad ID", emp_id="X1", **ok)
    raises("Rejects duplicate ID", emp_id="emp1001", **ok)
    raises("Rejects negative allowances", emp_id="EMP2000", **{**ok, "allowances": -1})
    raises("Rejects performance > 100", emp_id="EMP2000", **{**ok, "performance": 101})
    raises("Rejects non-numeric basic", emp_id="EMP2000", **{**ok, "basic": "abc"})
    raises("Rejects empty name", emp_id="EMP2000", **{**ok, "name": " "})
    return cases


st.set_page_config(page_title="Payroll & Tax Management System", page_icon="💼", layout="wide")
if "emps" not in st.session_state:
    st.session_state.emps = load()
emps = st.session_state.emps

st.title("Advanced Employee Payroll & Tax Management System")
st.caption("Phase III · Python Programming (N-PCCCM304P) · Bhushan Marbate [CM25074]")

tabs = st.tabs(["Dashboard", "Employees", "Add / Update", "Salary Slip",
                "Payroll Report", "Tax Slabs", "Self-Tests"])

rows = []
for eid, e in emps.items():
    s = calculate_salary(e)
    rows.append({"ID": eid, "Name": e["name"], "Basic": e["basic"], "Allowances": e["allowances"],
                 "Performance": e["performance"], "Bonus": s["bonus"], "Gross": s["gross"],
                 "PF": s["pf"], "Prof. Tax": s["prof_tax"], "Income Tax": s["income_tax"],
                 "Net": s["net"]})
df = pd.DataFrame(rows)

with tabs[0]:
    c = st.columns(4)
    c[0].metric("Employees", len(df))
    c[1].metric("Total gross", inr(df["Gross"].sum()) if len(df) else "-")
    c[2].metric("Total deductions", inr((df["PF"] + df["Prof. Tax"] + df["Income Tax"]).sum()) if len(df) else "-")
    c[3].metric("Total net payout", inr(df["Net"].sum()) if len(df) else "-")
    if len(df):
        st.bar_chart(df.set_index("Name")["Net"])
    if st.button("Reset to demo data"):
        st.session_state.emps = json.loads(json.dumps(DEMO))
        save(st.session_state.emps)
        st.rerun()

with tabs[1]:
    q = st.text_input("Search by ID or name")
    view = df
    if q and len(df):
        view = df[df["ID"].str.contains(q, case=False) | df["Name"].str.contains(q, case=False)]
    if len(view):
        st.dataframe(view[["ID", "Name", "Basic", "Performance", "Net"]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No records found.")
    if emps:
        st.subheader("Delete employee")
        del_id = st.selectbox("Select ID", list(emps), key="del_id")
        if st.button("Delete", type="primary"):
            del emps[del_id]
            save(emps)
            st.success("Employee record deleted successfully.")
            st.rerun()

with tabs[2]:
    mode = st.radio("Mode", ["Add new", "Update existing"], horizontal=True)
    editing = mode == "Update existing" and bool(emps)
    cur = {"name": "", "basic": 0.0, "allowances": 0.0, "performance": 0.0}
    sel = ""
    if editing:
        sel = st.selectbox("Employee to update", list(emps))
        cur = emps[sel]
    with st.form(f"emp_form_{mode}_{sel}"):
        emp_id = st.text_input("Employee ID", value=sel, disabled=editing, placeholder="EMP1004")
        name = st.text_input("Name", value=cur["name"])
        basic = st.number_input("Basic salary (₹)", min_value=0.0, value=float(cur["basic"]), step=500.0)
        allow = st.number_input("Allowances (₹)", min_value=0.0, value=float(cur["allowances"]), step=500.0)
        perf = st.number_input("Performance (0-100)", min_value=0.0, max_value=100.0,
                               value=float(cur["performance"]), step=1.0)
        if st.form_submit_button("Save employee", type="primary"):
            try:
                key, rec = validate(sel if editing else emp_id, name, basic, allow, perf,
                                    emps, editing=editing)
                emps[key] = rec
                save(emps)
                st.success("Employee updated successfully." if editing else "Employee added successfully.")
                st.rerun()
            except PayrollError as err:
                st.error(str(err))

with tabs[3]:
    if not emps:
        st.info("No employees available.")
    else:
        sid = st.selectbox("Employee ID", list(emps), key="slip_id")
        e, s = emps[sid], calculate_salary(emps[sid])
        st.subheader("Monthly Salary Slip")
        st.write(f"**{sid}** · {e['name']} · Performance {e['performance']:.0f}")
        slip = pd.DataFrame([
            ("Basic salary", e["basic"]), ("Allowances", e["allowances"]), ("Bonus", s["bonus"]),
            ("Gross salary", s["gross"]), ("Provident fund (12%)", s["pf"]),
            ("Professional tax", s["prof_tax"]), ("Income tax", s["income_tax"]),
            ("Total deductions", s["deductions"]), ("NET SALARY", s["net"])],
            columns=["Component", "Amount"])
        slip["Amount"] = slip["Amount"].map(inr)
        st.table(slip.set_index("Component"))

with tabs[4]:
    st.subheader("Consolidated Payroll Report")
    if len(df):
        rep = df[["ID", "Name", "Gross", "PF", "Prof. Tax", "Income Tax", "Net"]]
        st.dataframe(rep, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", rep.to_csv(index=False), "payroll_report.csv", "text/csv")
    else:
        st.info("No records.")

with tabs[5]:
    st.subheader("Company-defined demo tax slabs (monthly gross)")
    prev, srows = 0, []
    for limit, rate in TAX_SLABS:
        srows.append({"From": inr(prev), "To": "and above" if limit == float("inf") else inr(limit),
                      "Rate": f"{rate * 100:.0f}%"})
        prev = limit
    st.table(pd.DataFrame(srows).set_index("From"))
    st.caption("PF = 12% of basic · Professional tax = ₹200 if gross > ₹15,000 · "
               "Bonus: 15% (perf ≥ 90), 10% (≥ 75), 5% (≥ 60), else 0.")

with tabs[6]:
    results = run_tests()
    passed = sum(1 for _, ok_ in results if ok_)
    (st.success if passed == len(results) else st.error)(f"{passed}/{len(results)} tests passed")
    st.table(pd.DataFrame([(n, "PASS" if ok_ else "FAIL") for n, ok_ in results],
                          columns=["Test", "Result"]).set_index("Test"))
