import os
import glob

from flask import Blueprint, jsonify, request, abort, url_for\

from qiime.sdk import Artifact, Visualization

workspace = Blueprint('workspace', __name__)

ARTIFACTS = {}
VISUALIZATIONS = {}


def load_artifacts(**kwargs):
    return {k: Artifact.load(ARTIFACTS[v]) for k, v in kwargs.items()}


@workspace.route('/', methods=['GET'])
def get_workspace():
    return jsonify({'workspace': os.getcwd()})


@workspace.route('/', methods=['PUT'])
def change_workspace():
    request_body = request.get_json()
    new_dir = request_body['workspace']
    try:
        os.chdir(new_dir)
        return ''
    except Exception:
        # TODO: what's a good status code for this?
        abort(500)


def _result_record(result, name, route):
    return {
        'name': name,
        'uuid': str(result.uuid),
        'type': repr(result.type),
        'uri': url_for(route, uuid=result.uuid)
    }


@workspace.route('/artifacts', methods=['GET'])
def get_artifacts():
    global ARTIFACTS
    ARTIFACTS = {}
    path = os.getcwd()
    artifact_paths = list(glob.glob(os.path.join(path, '*.qza')))
    artifacts = []
    for artifact_path in artifact_paths:
        try:
            artifact = Artifact.load(artifact_path)
        except Exception:
            pass  # TODO: do better things when this happens
        name, _ = os.path.splitext(os.path.basename(artifact_path))
        artifacts.append(_result_record(artifact, name, '.inspect_artifact'))
        ARTIFACTS[artifact.uuid] = artifact_path

    return jsonify({'artifacts': artifacts})


@workspace.route('/artifacts/<uuid>', methods=['GET'])
def inspect_artifact(uuid):
    try:
        artifact = Artifact.load(ARTIFACTS[uuid])
    except Exception:
        abort(404)

    return jsonify({'uuid': artifact.uuid, 'type': artifact.type})


@workspace.route('/artifacts/<uuid>', methods=['DELETE'])
def delete_artifact(uuid):
    try:
        os.remove(ARTIFACTS[uuid])
        return ''
    except (OSError, KeyError):
        abort(404)


@workspace.route('/visualizations', methods=['GET'])
def get_visualizations():
    global VISUALIZATIONS
    VISUALIZATIONS = {}
    path = os.getcwd()
    viz_paths = list(glob.glob(os.path.join(path, '*.qzv')))
    visualizations = []
    for viz_path in viz_paths:
        try:
            viz = Visualization.load(viz_path)
        except Exception:
            pass  # TODO: do better things when this happens
        name, _ = os.path.splitext(os.path.basename(viz_path))
        VISUALIZATIONS[viz.uuid] = viz_path
        visualizations.append(
            _result_record(viz, name, '.inspect_visualization'))

    return jsonify({'visualizations': visualizations})


@workspace.route('/visualizations/<uuid>', methods=['GET'])
def inspect_visualization(uuid):
    try:
        visualization = Visualization.load(VISUALIZATIONS[uuid])
    except Exception:
        abort(404)

    return jsonify({'uuid': visualization.uuid, 'type': visualization.type})


@workspace.route('/visualizations/<uuid>', methods=['DELETE'])
def delete_visualization(uuid):
    try:
        os.remove(VISUALIZATIONS[uuid])
        return ''
    except (OSError, KeyError):
        abort(404)
