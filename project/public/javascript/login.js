async function submitForm(event) 
{
    event.preventDefault(); // Prevent the default form submission

    const form = document.getElementById('login-form');
    const formData = new FormData(form);

    const user_data = {
        username: formData.get('username'),
        password: formData.get('password'),
    };

    try 
    {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(user_data)
        });
        
        if (response.ok) 
        {
            const result = await response.json();
            
            if(result.error)
                addErrorCaption(result);
            else
                window.location.href = '/homepage';
        } 
        else 
        {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } 
    catch (error) 
    {
        alert('An error occurred: ' + error);
    }
}


function addErrorCaption(errordata)
{
    raiseSegmentNote("#loginError", "")

    raiseSegmentNote("#loginError", errordata.yaping)
}

function raiseSegmentNote(divid, yaping)
{
    let block = document.querySelector(divid);
    block.innerHTML = ``;
    html = `<label class="note">` + yaping + `</label>`;
    block.innerHTML = html;
}