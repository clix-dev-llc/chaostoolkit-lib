from copy import deepcopy
import threading
import time
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

from chaoslib.run import Runner
from chaoslib.types import Strategy

from fixtures import experiments


def run_http_server_in_background():
    def slow_app(environ, start_response):
        time.sleep(5)
        status = '200 OK'
        headers = [('Content-type', 'text/plain; charset=utf-8')]
        start_response(status, headers)
        return [b"Hello World"]

    def make_server(host, port, app):
        server = WSGIServer((host, port), WSGIRequestHandler)
        server.set_app(app)
        return server

    httpd = make_server('', 8700, slow_app)
    httpd.handle_request()


def test_play_rollbacks_on_graceful_exit_with_http_action():
    server = threading.Thread(target=run_http_server_in_background)
    server.start()

    x = deepcopy(experiments.ExperimentGracefulExitLongHTTPCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x, settings={
            "runtime": {"rollbacks": {"strategy": "always"}}})

        assert journal["status"] == "interrupted"
        assert len(journal["rollbacks"]) == 1

    server.join()


def test_do_not_play_rollbacks_on_graceful_exit_with_http_action():
    server = threading.Thread(target=run_http_server_in_background)
    server.start()

    x = deepcopy(experiments.ExperimentUngracefulExitLongHTTPCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x, settings={
            "runtime": {"rollbacks": {"strategy": "always"}}})

        assert journal["status"] == "interrupted"
        assert len(journal["rollbacks"]) == 0

    server.join()


def test_play_rollbacks_on_graceful_exit_with_process_action():
    x = deepcopy(experiments.ExperimentGracefulExitLongProcessCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x, settings={
            "runtime": {"rollbacks": {"strategy": "always"}}})

        assert journal["status"] == "interrupted"
        assert len(journal["rollbacks"]) == 1


def test_do_not_play_rollbacks_on_graceful_exit_with_process_action():
    x = deepcopy(experiments.ExperimentUngracefulExitLongProcessCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x, settings={
            "runtime": {"rollbacks": {"strategy": "always"}}})

        assert journal["status"] == "interrupted"
        assert len(journal["rollbacks"]) == 0


def test_play_rollbacks_on_graceful_exit_with_python_action():
    x = deepcopy(experiments.ExperimentGracefulExitLongPythonCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x, settings={
            "runtime": {"rollbacks": {"strategy": "always"}}})

        assert journal["status"] == "interrupted"
        assert len(journal["rollbacks"]) == 1


def test_do_not_play_rollbacks_on_graceful_exit_with_python_action():
    server = threading.Thread(target=run_http_server_in_background)
    server.start()

    x = deepcopy(experiments.ExperimentUngracefulExitLongHTTPCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x, settings={
            "runtime": {"rollbacks": {"strategy": "always"}}})

        assert journal["status"] == "interrupted"
        assert len(journal["rollbacks"]) == 0

    server.join()


def test_wait_for_background_activity_on_graceful_exit():
    server = threading.Thread(target=run_http_server_in_background)
    server.start()

    x = deepcopy(experiments.ExperimentGracefulExitLongHTTPCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x)

        assert journal["status"] == "interrupted"
        assert 3.0 < journal["run"][0]["duration"] < 3.2

    server.join()


def test_do_not_wait_for_background_activity_on_ungraceful_exit():
    server = threading.Thread(target=run_http_server_in_background)
    server.start()

    x = deepcopy(experiments.ExperimentUngracefulExitLongHTTPCall)
    with Runner(Strategy.DEFAULT) as runner:
        journal = runner.run(x)

        assert journal["status"] == "interrupted"
        assert journal["run"][0]["status"] == "failed"

    server.join()
