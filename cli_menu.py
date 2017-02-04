import sys
import timeit

from generate_dataset import GenerateDataset
from crf_suite import CrfSuite
from annotator import Annotator
from api import API
from logger import Logger
from evaluator import Evaluator

class CliMenu():
    __argument_train = "-t"
    __argument_optimise = "-o"
    __argument_annotate_dataset = "-a"
    __argument_api = "-rn"
    __argument_evaluate = "-e"

    def __init__(self):
        self.logger = Logger()
        self.logger.println("cli menu created")

    def perform_command(self):
        command_arg = sys.argv[1]

        if command_arg == self.__argument_train:
            if len(sys.argv) > 2:
                self.train_model(nr_of_files=int(sys.argv[2]))
            else:
                self.train_model()

        elif command_arg == self.__argument_optimise:
            self.optimise_model()

        elif command_arg == self.__argument_annotate_dataset:
            if len(sys.argv) > 2:
                self.annotate_data(nr_docs=int(sys.argv[2]))
            else:
                self.annotate_data()

        elif command_arg == self.__argument_api:
            self.run_api()

        elif command_arg == self.__argument_evaluate:
            if len(sys.argv) > 2:
                self.evaluate_model(sys.argv[2])
            else:
                print("evaluate model option needs an extra parameter")

        else:
            print("Commands accepted:")
            print("train: -t <number_of_documents>(default is all available documents")
            print("hyperparameter optimisation: -o")
            print("annotate dataset: -a <number_of_documents>(default is all available documents")
            print("run api: -rn")
            print("evaluate model: -e [-b train and analyse performance using bootstrapping]|[-r perform roc analysis]")

    def annotate_db_data(self):
        """
        gd = GenerateDataset()
        gd.pull_db_records(2, 1000)
        gd.tokenize_text()
        gd.pos_tag_tokens()
        gd.ner_tag_tokens()
        gd.nonlocal_ner_tag_tokens()
        gd.save_tagged_tokens()
        """
        raise NotImplementedError

    def annotate_data(self, nr_docs=-1):
        self.logger.println("data annotator called")
        start_time = timeit.default_timer()
        annotator = Annotator()
        annotator.prepare_dataset(nr_docs)
        elapsed_seconds = timeit.default_timer() - start_time
        self.logger.print_time_taken("data annotation operation took", elapsed_seconds)

    def optimise_model(self):
        self.logger.println("optimise model called")
        start_time = timeit.default_timer()
        cs = CrfSuite()
        cs.get_dataset()
        #cs.load_embeddings()
        cs.generate_embeddings()
        #cs.encode_dataset()

        cs.split_dataset()
        cs.generate_features()
        cs.optimise_model()
        elapsed_seconds = timeit.default_timer() - start_time
        self.logger.print_time_taken("optimise model operation took", elapsed_seconds)

    def train_model(self, nr_of_files=-1):
        self.logger.println("train model called")
        start_time = timeit.default_timer()
        cs = CrfSuite()
        cs.get_dataset(nr_of_files=nr_of_files)
        #cs.load_embeddings()
        cs.generate_embeddings()
        cs.encode_dataset()

        cs.split_dataset()
        cs.generate_features()
        cs.train_model()
        cs.test_model()
        elapsed_seconds = timeit.default_timer() - start_time
        self.logger.print_time_taken("train model operation took", elapsed_seconds)

    def run_api(self):
        self.logger.println("api called")
        api = API()
        api.run()

    def evaluate_model(self, arg):
        self.logger.println("evaluate model called")
        evaluator = Evaluator()


if __name__ == '__main__':
    CliMenu().perform_command()