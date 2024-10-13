const mainupload = document.getElementById("main-upload");
const dropZone = document.getElementById('drop-zone');

let folderTree = {};
let interval;
let progress = 0;
let isStopped = false;
let currentFile = null;

const validFileTypes = ['application/zip', 'application/x-zip-compressed', 'multipart/x-zip'];

document.getElementById('upload-icon').addEventListener('click', () => {
    document.getElementById('file-input').click();
});

document.getElementById('file-input').addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file && validFileTypes.includes(file.type)) {
        resetProgress();
        uploadFile(file);
    } else {
        alert("Only ZIP files are allowed!");
        event.target.value = "";
    }
});

document.getElementById('drag-drop-area').style.display = "block";
document.getElementById('upload-area').style.display = "none";

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('highlight'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('highlight'), false);
});

dropZone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (file && validFileTypes.includes(file.type)) {
        resetProgress();
        uploadFile(file);
    } else {
        alert("Only ZIP files are allowed!");
    }
});

function uploadFile(file) {
    document.getElementById('drag-drop-area').style.display = "none";
    document.getElementById('upload-area').style.display = "flex";
    folderTree = {};
    document.getElementById('file-structure').innerHTML = '';
    document.getElementById('file-display').innerHTML = '';
    currentFile = file;
    startUploadProgress(file);
}

function startUploadProgress(file) {
    interval = setInterval(() => {
        if (progress < 100) {
            updateProgressUI(++progress);
        } else {
            clearInterval(interval);
            showDonePage();
            extractZip(file);
        }
    }, 50);
}

function updateProgressUI(progress) {
    document.querySelector('.progress').style.setProperty('--progress', `${progress}%`);
    document.getElementById('progress-text').textContent = `${progress}%`;
}

function extractZip(file) {
    const reader = new FileReader();
    reader.onload = (event) => {
        JSZip.loadAsync(event.target.result).then((zip) => {
            const fileStructure = document.getElementById('file-structure');
            Object.keys(zip.files).forEach((fileName) => {
                let currentFolder = folderTree;
                fileName.split('/').forEach((part, index, arr) => {
                    currentFolder = currentFolder[part] = (index === arr.length - 1) ? null : currentFolder[part] || {};
                });
            });
            displayFolderContents(folderTree, fileStructure, zip, []);
        });
    };
    reader.readAsArrayBuffer(file);
}

const icons = {
    stop: document.getElementById('image-paths').getAttribute('data-stop-icon'),
    pause: document.getElementById('image-paths').getAttribute('data-pause-icon'),
    txt: document.getElementById('image-paths').getAttribute('data-txt-icon'),
    json: document.getElementById('image-paths').getAttribute('data-json-icon'),
    xml: document.getElementById('image-paths').getAttribute('data-xml-icon'),
    file: document.getElementById('image-paths').getAttribute('data-file-icon'),
    folder: document.getElementById('image-paths').getAttribute('data-folder-icon')
};

function displayFolderContents(folder, container, zip, path) {
    container.innerHTML = '';
    if (path.length) {
        const backButton = document.createElement('div');
        backButton.innerHTML = `<span class="inline-block text-lg mr-2">&larr;</span>Back`;
        backButton.classList.add('cursor-pointer', 'text-gray-500', 'mb-4', 'flex', 'items-center', 'text-sm');
        backButton.addEventListener('click', () => {
            const parentFolder = path.slice(0, -1).reduce((acc, part) => acc[part], folderTree);
            displayFolderContents(parentFolder, container, zip, path.slice(0, -1));
        });
        container.appendChild(backButton);
    }

    Object.keys(folder).forEach((item) => {
        if (item !== '') {
            const itemPath = path.concat(item).join('/');
            const isFile = folder[item] === null;
            const fileElement = document.createElement('div');
            fileElement.classList.add('cursor-pointer', isFile ? 'text-blue-300' : 'text-yellow-300', 'mb-2');
            fileElement.innerHTML = `<img src="${icons[isFile ? getIcon(item) : 'folder']}" class="inline-block w-5 h-5 mr-2" alt="">${item}`;

            fileElement.addEventListener('click', async () => {

                const previouslySelected = document.querySelector('.selected-file');
                if (previouslySelected) {
                    previouslySelected.classList.remove('selected-file');
                }

                fileElement.classList.add('selected-file');

                if (isFile) {
                    const fileData = await zip.file(itemPath).async('blob');
                    renderFile(fileData, item);
                } else {
                    displayFolderContents(folder[item], container, zip, path.concat(item));
                }
            });
            container.appendChild(fileElement);
        }
    });
}

function getIcon(item) {
    if (item.endsWith('.txt') || item.endsWith('.log')) return 'txt';
    if (item.endsWith('.json')) return 'json';
    if (item.endsWith('.xml')) return 'xml';
    return 'file';
}

function renderFile(fileData, item) {
    const fileDisplay = document.getElementById('file-display');
    fileDisplay.innerHTML = '';

    if (item.endsWith('.txt') || item.endsWith('.log')) {
        const reader = new FileReader();
        reader.onload = (e) => fileDisplay.appendChild(createElement('pre', e.target.result));
        reader.readAsText(fileData);
    } else if (item.endsWith('.json')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const jsonData = JSON.parse(e.target.result);
                fileDisplay.appendChild(createElement('pre', JSON.stringify(jsonData, null, 2)));
            } catch (err) {
                alert('Error parsing JSON file. (please open the `pretty` directory if exists, and read json files)');
            }
        };
        reader.readAsText(fileData);
    } else if (item.endsWith('.xml')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(e.target.result, "application/xml");
            const xmlSerializer = new XMLSerializer();
            const prettyXML = xmlSerializer.serializeToString(xmlDoc);
            fileDisplay.appendChild(createElement('pre', prettyXML));
        };
        reader.readAsText(fileData);
    } else {
        alert(`Cannot open ${item}: Unsupported file type`);
    }
}

function createElement(tag, text, attributes = {}) {
    const element = document.createElement(tag);
    if (text) element.textContent = text;
    Object.keys(attributes).forEach(attr => element.setAttribute(attr, attributes[attr]));
    return element;
}

document.getElementById('stop-icon').addEventListener('click', toggleUploadState);

function toggleUploadState() {
    isStopped = !isStopped;
    clearInterval(interval);
    document.getElementById('stop-icon').src = icons[isStopped ? 'pause' : 'stop'];
    if (!isStopped && currentFile) startUploadProgress(currentFile);
}

document.getElementById('close-icon').addEventListener('click', resetAll);

function showDonePage() {
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('done').style.display = 'grid';
}

function resetProgress() {
    progress = 0;
    isStopped = false;
    clearInterval(interval);
    updateProgressUI(0);
    document.getElementById('stop-icon').src = icons.stop;
    document.getElementById('file-input').value = "";
}

document.getElementById("open").addEventListener("click", () => {
    toggleUploadVisibility(false);
});

document.getElementById("close-back-link").addEventListener("click", () => {
    toggleUploadVisibility(true);
});

function toggleUploadVisibility(isUploadVisible) {
    document.getElementById("back-link").style.display = isUploadVisible ? "none" : "block";
    mainupload.style.display = isUploadVisible ? "block" : "none";
}

document.getElementById("send-another").addEventListener("click", () => {
    resetProgress();
    document.getElementById('drag-drop-area').style.display = "flex";
    document.getElementById('upload-area').style.display = "none";
    document.getElementById('done').style.display = "none";
});

function resetAll() {
    clearInterval(interval);
    resetProgress();
    document.getElementById('upload-area').style.display = "none";
    document.getElementById('drag-drop-area').style.display = "flex";
}
