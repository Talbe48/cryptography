async function EncryptPress()
{
    const fileInput = document.getElementById('filepath');
    const file = fileInput.files[0];

    if (!file) 
    {
        alert('No file selected');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/encrypt', {
            method: 'POST',
            body: formData
        });

        
        if (!response.ok) 
        {
            throw new Error('File upload failed');
        }

        const contentDisposition = response.headers.get('Content-Disposition');
        const firstQuoteIndex = contentDisposition.indexOf('"');
        const secondQuoteIndex = contentDisposition.indexOf('"', firstQuoteIndex + 1);
        const filename = contentDisposition.substring(firstQuoteIndex + 1, secondQuoteIndex);

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => URL.revokeObjectURL(downloadUrl), 100);

        fileInput.value = '';
    } 
    catch (error) 
    {
        alert('Error: ' + error.message);
    }
}


async function DecryptPress()
{
    const fileInput = document.getElementById('filepath');
    const file = fileInput.files[0];

    if (!file) 
    {
        alert('No file selected');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/decrypt', {
            method: 'POST',
            body: formData
        });

        
        if (!response.ok) {
            throw new Error('File upload failed');
        }

        const contentDisposition = response.headers.get('Content-Disposition');
        const firstQuoteIndex = contentDisposition.indexOf('"');
        const secondQuoteIndex = contentDisposition.indexOf('"', firstQuoteIndex + 1);
        const filename = contentDisposition.substring(firstQuoteIndex + 1, secondQuoteIndex);

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => URL.revokeObjectURL(downloadUrl), 100);

        fileInput.value = '';
    } 
    catch (error) 
    {
        alert('Error: ' + error.message);
    }
}


async function BackUpPress()
{
    const fileInput = document.getElementById('filepath');
    const file = fileInput.files[0];

    if (!file) 
    {
        alert('No file selected');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/uploadbackup', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) 
            {
            throw new Error('File upload failed');
        }
        alert("file uploaded successfully")
    }
    catch (error) 
    {
        alert('Error: ' + error.message);
    }
}

async function GetBackup()
{
    try {
        const response = await fetch('/getbackup', {
            method: 'POST'
        });

        if(!response.ok) 
        {
            throw new Error('Server Error');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'backup.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } 
    catch (error) 
    {
        alert(error);
    }
}

async function DeleteBackup()
{
    if(!DeletConfirmation())
        return;

    try 
    {
        const response = await fetch("/deletebackup", {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        alert(result.info);
    } 
    catch(error) 
    {
        console.error("Failed to delete backup:", error);
        alert("Failed to delete backup. Please try again.");
    }
}

function DeletConfirmation()
{
    let confirmation = document.getElementById('confirmation').value
    if(confirmation != "delete")
    {
        raiseSegmentNote("#deldiv", false);
        return false;
    }
    raiseSegmentNote("#deldiv", true);
    return true;
}

function raiseSegmentNote(divid, hidden)
{
    let html;
    let block = document.querySelector(divid);
    block.innerHTML = ``;
    if(hidden)
        html = `<label hidden>type "delete" to confirm:</label> <input hidden type="text" id="confirmation" class="delinput">`;
    else
        html = `<label>type "delete" to confirm:</label> <input type="text" id="confirmation" class="delinput">`;
    block.innerHTML = html;
}