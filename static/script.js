function login(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            window.location.href = '/dashboard';
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        alert('Error during login. Please try again.');
    });
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/';
    }
}

// Load all data when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, fetching resources...');
    loadResources();
});

function loadResources() {
    console.log('Making request to /api/resources...');
    fetch('/api/resources')
        .then(res => {
            console.log('Response status:', res.status);
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            console.log('Resources loaded:', data);
            if (!Array.isArray(data)) {
                console.error('Expected array of resources, got:', data);
                return;
            }
            
            const resourcesList = document.getElementById('resourcesList');
            if (!resourcesList) {
                console.error('Could not find resourcesList element');
                return;
            }

            if (data.length === 0) {
                resourcesList.innerHTML = `
                    <tr>
                        <td colspan="4" style="text-align: center; padding: 2rem;">
                            No resources found. Add your first resource above.
                        </td>
                    </tr>
                `;
                return;
            }

            resourcesList.innerHTML = data.map(resource => `
                <tr>
                    <td>
                        <div class="resource-name">${resource.name}</div>
                    </td>
                    <td>${resource.max_units}</td>
                    <td>
                        <div class="progress-container">
                            <div class="quantity-display">
                                ${resource.available_quantity} / ${resource.max_units}
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" 
                                     style="width: ${(resource.available_quantity / resource.max_units) * 100}%">
                                </div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <div class="quantity-controls">
                            <button class="quantity-btn remove-btn" 
                                    onclick="updateQuantity('${resource.name}', -1)">
                                -
                            </button>
                            <button class="quantity-btn add-btn" 
                                    onclick="updateQuantity('${resource.name}', 1)">
                                +
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        })
        .catch(error => {
            console.error('Error loading resources:', error);
            const resourcesList = document.getElementById('resourcesList');
            resourcesList.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; color: red; padding: 2rem;">
                        Error loading resources. Please try refreshing the page.
                    </td>
                </tr>
            `;
        });
}

function addResource() {
    const nameInput = document.getElementById('newResource');
    const maxUnitsInput = document.getElementById('maxUnits');
    
    const name = nameInput.value.trim();
    const maxUnits = parseInt(maxUnitsInput.value);
    
    if (!name || !maxUnits) {
        alert('Please enter both resource name and maximum units');
        return;
    }

    console.log('Adding resource:', { name, maxUnits });

    fetch('/api/resources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            name: name,
            max_units: maxUnits
        })
    })
    .then(res => {
        console.log('Add resource response status:', res.status);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log('Add resource response:', data);
        if (data.error) {
            alert(data.error);
        } else {
            nameInput.value = '';
            maxUnitsInput.value = '';
            loadResources();  // Reload the resources list
        }
    })
    .catch(error => {
        console.error('Error adding resource:', error);
        alert('Error adding resource. Please try again.');
    });
}

function updateQuantity(resourceName, change) {
    console.log('Updating quantity:', { resourceName, change });

    fetch(`/api/resources/${resourceName}/quantity`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ change })
    })
    .then(res => {
        console.log('Update quantity response status:', res.status);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log('Update quantity response:', data);
        if (data.error) {
            alert(data.error);
        } else {
            loadResources();  // Reload the resources list
        }
    })
    .catch(error => {
        console.error('Error updating quantity:', error);
        alert('Error updating quantity. Please try again.');
    });
}
