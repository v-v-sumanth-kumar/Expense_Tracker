import { useCallback, useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "https://expense-tracker-m530.onrender.com";

const initialForm = {
  amount: "",
  category: "",
  description: "",
  date: "",
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [expenses, setExpenses] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sortByDateDesc, setSortByDateDesc] = useState(true);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const loadExpenses = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (categoryFilter) {
        params.set("category", categoryFilter);
      }
      if (sortByDateDesc) {
        params.set("sort", "date_desc");
      }
      const queryString = params.toString();
      const response = await fetch(`${API_BASE_URL}/expenses${queryString ? `?${queryString}` : ""}`);
      if (!response.ok) {
        throw new Error("Could not fetch expenses.");
      }
      const data = await response.json();
      setExpenses(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, sortByDateDesc]);

  useEffect(() => {
    loadExpenses();
  }, [loadExpenses]);

  const total = useMemo(() => {
    return expenses.reduce((sum, expense) => sum + Number(expense.amount), 0);
  }, [expenses]);

  const availableCategories = useMemo(() => {
    const categories = new Set(expenses.map((expense) => expense.category));
    if (form.category) {
      categories.add(form.category);
    }
    return [...categories].sort((a, b) => a.localeCompare(b));
  }, [expenses, form.category]);

  const onSubmit = async (event) => {
    event.preventDefault();
    if (submitting) {
      return;
    }

    setSubmitting(true);
    setError("");
    const idempotencyKey = crypto.randomUUID();

    try {
      const response = await fetch(`${API_BASE_URL}/expenses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({
          amount: form.amount,
          category: form.category.trim(),
          description: form.description.trim(),
          date: form.date,
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not save expense.");
      }

      setForm(initialForm);
      await loadExpenses();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="container">
      <h1>Expense Tracker</h1>

      <section className="card">
        <h2>Add Expense</h2>
        <form className="expense-form" onSubmit={onSubmit}>
          <label>
            Amount (INR)
            <input
              type="number"
              step="0.01"
              min="0.01"
              required
              value={form.amount}
              onChange={(e) => setForm((prev) => ({ ...prev, amount: e.target.value }))}
            />
          </label>

          <label>
            Category
            <input
              type="text"
              required
              value={form.category}
              onChange={(e) => setForm((prev) => ({ ...prev, category: e.target.value }))}
            />
          </label>

          <label>
            Description
            <input
              type="text"
              required
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
            />
          </label>

          <label>
            Date
            <input
              type="date"
              required
              value={form.date}
              onChange={(e) => setForm((prev) => ({ ...prev, date: e.target.value }))}
            />
          </label>

          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Save expense"}
          </button>
        </form>
      </section>

      <section className="card">
        <div className="toolbar">
          <label>
            Filter by category
            <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
              <option value="">All categories</option>
              {availableCategories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={sortByDateDesc}
              onChange={(e) => setSortByDateDesc(e.target.checked)}
            />
            Sort by date (newest first)
          </label>

          <button type="button" onClick={loadExpenses} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        <p className="total">Total: {formatCurrency(total)}</p>

        {error ? <p className="error">{error}</p> : null}

        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Category</th>
              <th>Description</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {expenses.length === 0 ? (
              <tr>
                <td colSpan={4} className="empty">
                  {loading ? "Loading expenses..." : "No expenses found."}
                </td>
              </tr>
            ) : (
              expenses.map((expense) => (
                <tr key={expense.id}>
                  <td>{expense.date}</td>
                  <td>{expense.category}</td>
                  <td>{expense.description}</td>
                  <td>{formatCurrency(Number(expense.amount))}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}

export default App;
