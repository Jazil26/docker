from flask import Flask, render_template, request, jsonify
import platform
import psutil
import socket
import docker

app = Flask(__name__)

def check_os_type_and_version():
    os_type = platform.system()
    os_version = platform.version()
    os_release = platform.release()
    return f"OS Type: {os_type}, OS Version: {os_version}, OS Release: {os_release}"

def get_hardware_details():
    hardware_info = {
        "Processor": platform.processor(),
        "Physical Cores": psutil.cpu_count(logical=False),
        "Total Cores": psutil.cpu_count(logical=True),
        "RAM": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"
    }
    return hardware_info

def test_network_connection(host="www.google.com", port=80):
    try:
        socket.create_connection((host, port), timeout=5)
        return f"Connection to {host}:{port} is successful."
    except socket.error as e:
        return f"Connection to {host}:{port} failed: {e}"

def run_docker_container(image_name, host_port=None):
    client = docker.from_env()
    if image_name != image_name.lower():
        return f"Error: Docker image name '{image_name}' must be lowercase."
    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        try:
            client.images.pull(image_name)
        except docker.errors.APIError as e:
            return f"Failed to pull image '{image_name}': {e}"
    try:
        ports = {'80/tcp': host_port} if host_port else {}
        container = client.containers.run(image_name, detach=True, ports=ports)
        container_info = client.containers.get(container.id)
        return {
            "Container ID": container_info.id,
            "Status": container_info.status,
            "Image": container_info.image.tags,
            "Created": container_info.attrs['Created'],
            "Network Settings": container_info.attrs['NetworkSettings'],
            "Ports": container_info.attrs['NetworkSettings']['Ports']
        }
    except docker.errors.APIError as e:
        return f"Failed to run container: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/system_info')
def system_info():
    return jsonify({
        "os_info": check_os_type_and_version(),
        "hardware_info": get_hardware_details(),
        "network_test": test_network_connection()
    })

@app.route('/docker', methods=['POST'])
def docker_management():
    data = request.json
    image_name = data.get('image_name')
    host_port = data.get('host_port')
    if host_port:
        try:
            host_port = int(host_port)
            if not (0 < host_port <= 65535):
                return jsonify({"error": "Invalid port number. Port must be between 1 and 65535."}), 400
        except ValueError:
            return jsonify({"error": "Invalid port number. Please enter a valid integer."}), 400
    result = run_docker_container(image_name, host_port)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
