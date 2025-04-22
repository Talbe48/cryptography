
async function submitForm(event) 
{
    event.preventDefault(); // Prevent the default form submission

    const form = document.getElementById('register-form');
    const formData = new FormData(form);

    const user_data = {
        username: formData.get('username'),
        password: formData.get('password'),
        repassword: formData.get('repassword')
    };

    try 
    {
        const response = await fetch('/register', {
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
    removeSegmentNote("#userError")
    removeSegmentNote("#passError")
    removeSegmentNote("#repassError")

    if(errordata.unvalid == "username")
        raiseSegmentNote("#userError", errordata.yaping)

    if(errordata.unvalid == "password")
        raiseSegmentNote("#passError", errordata.yaping)
    
    if(errordata.unvalid == "repassword")
        raiseSegmentNote("#repassError", errordata.yaping)
}

function raiseSegmentNote(divid, yaping)
{
    let block = document.querySelector(divid);
    block.innerHTML = ``;
    html = `<label class="note">` + yaping + `</label>`;
    block.innerHTML = html;
}

function removeSegmentNote(divid)
{
    let block = document.querySelector(divid);
    block.innerHTML = ``;
}