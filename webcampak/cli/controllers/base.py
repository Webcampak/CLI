"""Webcampak base controller."""

from cement.core.controller import CementBaseController, expose

class wpakBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = 'Webcampak is a set of tools to reliably capture high definition pictures, at pre-defined interval, over a very long period of time and automatically generate timelapse videos. Built to scale and adapt to a variety of use cases, Webcampak will drive a DSLR camera from projects ranging from 6 months to years. Failsafe mechanisms are available to ensure no pictures get lost during that time.'
        arguments = [
            #(['-f', '--foo'],
            # dict(help='the notorious foo option', dest='foo', action='store',
            #      metavar='TEXT') ),
            ]

    @expose(hide=True)
    def default(self):
        print("Inside wpakBaseController.default().")

        # If using an output handler such as 'mustache', you could also
        # render a data dictionary using a template.  For example:
        #
        #   data = dict(foo='bar')
        #   self.app.render(data, 'default.mustache')
        #
        #
        # The 'default.mustache' file would be loaded from
        # ``webcampak.cli.templates``, or ``/var/lib/webcampak/templates/``.
        #
        
