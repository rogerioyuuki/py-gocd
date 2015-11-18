import time

from gocd.api.response import Response
from gocd.api.endpoint import Endpoint


class Pipeline(Endpoint):
    base_path = 'go/api/pipelines/{id}'
    id = 'name'

    def __init__(self, server, name):
        """A wrapper for the `Go pipeline API`__

        .. __: http://api.go.cd/current/#pipelines

        Args:
          server (Server): A configured instance of
            :class:gocd.server.Server
          name (str): The name of the pipeline we're working on
        """
        self.server = server
        self.name = name

    def history(self, offset=0):
        """Lists previous instances/runs of the pipeline

        See the `Go pipeline history documentation`__ for example responses.

        .. __: http://api.go.cd/current/#get-pipeline-history

        Args:
          offset (int, optional): How many instances to skip for this response.

        Returns:
          Response: :class:`gocd.api.response.Response` object
        """
        return self._get('/history/{offset:d}'.format(offset=offset or 0))

    def release(self):
        """Releases a previously locked pipeline

        See the `Go pipeline release lock documentation`__ for example
        responses.

        .. __: http://api.go.cd/current/#releasing-a-pipeline-lock

        Returns:
          Response: :class:`gocd.api.response.Response` object
        """
        return self._post('/releaseLock')
    #: This is an alias for :meth:`release`
    unlock = release

    def pause(self, reason=''):
        """Pauses the current pipeline

        See the `Go pipeline pause documentation`__ for example responses.

        .. __: http://api.go.cd/current/#pause-a-pipeline

        Args:
          reason (str, optional): The reason the pipeline is being paused.

        Returns:
          Response: :class:`gocd.api.response.Response` object
        """
        return self._post('/pause', pauseCause=reason)

    def unpause(self):
        """Unpauses the pipeline

        See the `Go pipeline unpause documentation`__ for example responses.

        .. __: http://api.go.cd/current/#unpause-a-pipeline

        Returns:
          Response: :class:`gocd.api.response.Response` object
        """
        return self._post('/unpause')

    def status(self):
        """Returns the current status of this pipeline

        See the `Go pipeline status documentation`__ for example responses.

        .. __: http://api.go.cd/current/#get-pipeline-status

        Returns:
          Response: :class:`gocd.api.response.Response` object
        """
        return self._get('/status')

    def instance(self, counter=None):
        """Returns all the information regarding a specific pipeline run

        See the `Go pipeline instance documentation`__ for examples.

        .. __: http://api.go.cd/current/#get-pipeline-instance

        Args:
          counter (int): The pipeline instance to fetch.
            If falsey returns the latest pipeline instance from :meth:`history`.

        Returns:
          Response: :class:`gocd.api.response.Response` object
        """
        if not counter:
            history = self.history()
            if not history:
                return history
            else:
                return Response._from_json(history['pipelines'][0])

        return self._get('/instance/{counter:d}'.format(counter=counter))

    def schedule(self, variables=None, secure_variables=None, materials=None,
                 return_new_instance=False, backoff_time=1.0):
        """Schedule a pipeline run

        Aliased as :meth:`run`, :meth:`schedule`, and :meth:`trigger`.

        Args:
          variables (dict, optional): Variables to set/override
          secure_variables (dict, optional): Secure variables to set/override
          materials (dict, optional): Material revisions to be used for
            this pipeline run. The exact format for this is a bit iffy,
            have a look at the official
            `Go pipeline scheduling documentation`__ or inspect a call
            from triggering manually in the UI.
          return_new_instance (bool): Returns a :meth:`history` compatible
            response for the newly scheduled instance. This is primarily so
            users easily can get the new instance number. **Note:** This is done
            in a very naive way, it just checks that the instance number is
            higher than before the pipeline was triggered.
          backoff_time (float): How long between each check for
            :arg:`return_new_instance`.

         .. __: http://api.go.cd/current/#scheduling-pipelines

        Returns:
          Response: :class:`gocd.api.response.Response` object
        """
        scheduling_args = dict(
            variables=variables,
            secure_variables=secure_variables,
            material_fingerprint=materials,
        )

        scheduling_args = dict((k, v) for k, v in scheduling_args.items() if v is not None)

        # TODO: Replace this with whatever is the official way as soon as gocd#990 is fixed.
        # https://github.com/gocd/gocd/issues/990
        if return_new_instance:
            last_run = self.history()['pipelines'][0]['counter']
            response = self._post('/schedule', ok_status=202, **scheduling_args)
            if not response:
                return response

            max_tries = 10
            while max_tries > 0:
                current = self.instance()
                if current['counter'] > last_run:
                    return current
                else:
                    time.sleep(backoff_time)
                    max_tries -= 1

            # I can't come up with a scenario in testing where this would happen, but it seems
            # better than returning None.
            return response
        else:
            return self._post('/schedule', ok_status=202, **scheduling_args)
    #: This is an alias for :meth:`schedule`
    run = schedule
    #: This is an alias for :meth:`schedule`
    trigger = schedule
