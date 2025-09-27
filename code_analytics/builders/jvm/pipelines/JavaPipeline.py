from code_analytics.Builder import PipelineComponent


class JavaRunner(PipelineComponent):
    def __init__(self, jar_path: str = 'app.jar'):
        self.jar_path = jar_path

    def contribute(self, sections: dict):
        sections['cmd'].append(f'CMD ["java", "-jar", "{self.jar_path}"]')