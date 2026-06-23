const form = document.getElementById("item-form");
const itemsList = document.getElementById("items-list");
const emptyState = document.getElementById("empty-state");
const formMessage = document.getElementById("form-message");
const listMessage = document.getElementById("list-message");
const refreshBtn = document.getElementById("refresh-btn");

function showMessage(element, text, type) {
  element.textContent = text;
  element.className = `message ${type}`;
  element.hidden = false;
}

function hideMessage(element) {
  element.hidden = true;
  element.textContent = "";
}

function renderItems(items) {
  itemsList.innerHTML = "";

  if (items.length === 0) {
    emptyState.hidden = false;
    return;
  }

  emptyState.hidden = true;

  for (const item of items) {
    const li = document.createElement("li");
    li.className = "item";

    const name = document.createElement("div");
    name.className = "item-name";
    name.textContent = item.name;

    li.appendChild(name);

    if (item.description) {
      const description = document.createElement("p");
      description.className = "item-description";
      description.textContent = item.description;
      li.appendChild(description);
    }

    const id = document.createElement("p");
    id.className = "item-id";
    id.textContent = item.id;
    li.appendChild(id);

    itemsList.appendChild(li);
  }
}

async function loadItems() {
  hideMessage(listMessage);

  try {
    const response = await fetch("/items");
    if (!response.ok) {
      throw new Error(`Failed to load items (${response.status})`);
    }

    const items = await response.json();
    renderItems(items);
  } catch (error) {
    showMessage(listMessage, error.message, "error");
    emptyState.hidden = true;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage(formMessage);

  const name = document.getElementById("name").value.trim();
  const description = document.getElementById("description").value.trim();

  const payload = { name };
  if (description) {
    payload.description = description;
  }

  try {
    const response = await fetch("/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Failed to create item (${response.status})`);
    }

    form.reset();
    showMessage(formMessage, "Item added.", "success");
    await loadItems();
  } catch (error) {
    showMessage(formMessage, error.message, "error");
  }
});

refreshBtn.addEventListener("click", loadItems);

loadItems();
