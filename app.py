from flask import Flask, render_template, request, redirect
from datetime import date, timedelta
import json
import os

app = Flask(__name__)
TASK_FILE = 'tasks.json'


# Load tasks from JSON
def load_tasks():
    if not os.path.exists(TASK_FILE):
        return []
    try:
        with open(TASK_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


# Save tasks to JSON
def save_tasks(tasks):
    with open(TASK_FILE, 'w') as f:
        json.dump(tasks, f, indent=4)


# Priority sorting helper
def sort_tasks(tasks):
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    tasks.sort(key=lambda t: priority_order.get(t.get('priority', 'Medium'), 99))
    return tasks


@app.route('/', methods=['GET', 'POST'])
def home():
    today = date.today()
    today_str = today.isoformat()
    tomorrow_str = (today + timedelta(days=1)).isoformat()

    tasks = load_tasks()
    task_id_counter = max([t.get('id', 0) for t in tasks], default=0) + 1

    if request.method == 'POST':
        action = request.form.get('action')

        # Add task
        if action == 'add':
            due_date = request.form.get('due_date') or today_str
            task = {
                'id': task_id_counter,
                'name': request.form.get('name', '').strip(),
                'description': request.form.get('description', '').strip() or "No description",
                'priority': request.form.get('priority', 'Medium'),
                'status': 'Pending',
                'due_date': due_date.strip()
            }
            tasks.append(task)
            task_id_counter += 1

        # Delete task
        elif action == 'delete':
            try:
                task_id = int(request.form.get('id'))
                tasks = [t for t in tasks if t.get('id') != task_id]
            except:
                pass

        # Edit task (full edit from modal)
        elif action == 'edit':
            try:
                task_id = int(request.form.get('id'))
            except:
                task_id = None

            if task_id is not None:
                for t in tasks:
                    if t.get('id') == task_id:
                        # Update all editable fields (if provided)
                        t['name'] = request.form.get('name', t.get('name')).strip()
                        t['description'] = request.form.get('description', t.get('description')).strip() or "No description"
                        t['priority'] = request.form.get('priority', t.get('priority'))
                        t['status'] = request.form.get('status', t.get('status'))
                        t['due_date'] = request.form.get('due_date', t.get('due_date')).strip()
                        break

        save_tasks(tasks)
        return redirect('/')

    # Mark overdue tasks (optional behavior: we keep them but can mark priority)
    for t in tasks:
        if t.get('due_date', '') < today_str and t.get('status') == 'Pending':
            # don't change user's explicit priority, only ensure visibility — we'll keep priority but could mark overdue in UI
            t.setdefault('overdue', True)
        else:
            t.pop('overdue', None)

    # Sort tasks by priority (High -> Medium -> Low)
    tasks = sort_tasks(tasks)

    # Split tasks
    todays_tasks = [t for t in tasks if t.get('due_date') == today_str]
    tomorrows_tasks = [t for t in tasks if t.get('due_date') == tomorrow_str]
    upcoming_tasks = [t for t in tasks if t.get('due_date') > tomorrow_str]

    return render_template('index.html',
                           todays_tasks=todays_tasks,
                           tomorrows_tasks=tomorrows_tasks,
                           upcoming_tasks=upcoming_tasks,
                           today=today_str,
                           tomorrow=tomorrow_str)


if __name__ == '__main__':
    app.run(debug=True)
