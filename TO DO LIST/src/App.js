import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [tasks, setTasks] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [editTaskId, setEditTaskId] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  const API_URL = "http://127.0.0.1:8000/api/tasks/";

  const fetchTasks = () => {
    axios.get(API_URL)
      .then(res => setTasks(res.data))
      .catch(err => console.error("Error fetching tasks:", err));
  };

  const addTask = (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    axios.post(API_URL, { title: newTaskTitle, completed: false })
      .then(() => {
        setNewTaskTitle("");
        fetchTasks();
      })
      .catch(err => console.error("Error adding task:", err));
  };

  const toggleComplete = (task) => {
    axios.put(`${API_URL}${task._id}/`, {
      title: task.title,
      completed: !task.completed,
    }).then(fetchTasks)
      .catch(err => console.error("Error updating completion:", err));
  };

  const deleteTask = (taskId) => {
    axios.delete(`${API_URL}${taskId}/`)
      .then(fetchTasks)
      .catch(err => console.error("Error deleting task:", err));
  };

  const startEdit = (task) => {
    setEditTaskId(task._id);
    setEditTitle(task.title);
  };

  const saveEdit = (task) => {
    axios.put(`${API_URL}${task._id}/`, {
      title: editTitle,
      completed: task.completed,
    }).then(() => {
      setEditTaskId(null);
      setEditTitle("");
      fetchTasks();
    }).catch(err => console.error("Error updating task:", err));
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div className="App">
      <h1>To-Do List</h1>

      <form onSubmit={addTask}>
        <input
          type="text"
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          placeholder="Add new task..."
        />
        <button type="submit">Add</button>
      </form>

      <ul>
        {tasks.map(task => (
          <li key={task._id}>
            <input
              type="checkbox"
              checked={task.completed}
              onChange={() => toggleComplete(task)}
            />
            {editTaskId === task._id ? (
              <>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                />
                <button onClick={() => saveEdit(task)}>Save</button>
              </>
            ) : (
              <>
                <span style={{ textDecoration: task.completed ? "line-through" : "none" }}>
                  {task.title}
                </span>
                <button onClick={() => startEdit(task)}>Edit</button>
              </>
            )}
            <button onClick={() => deleteTask(task._id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
