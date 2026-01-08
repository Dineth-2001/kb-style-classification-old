# import unittest
# from text_compare import get_similarity_score


# class TestTextCompare(unittest.TestCase):

#     def test_similarity_score_op1_op2(self):
#         op1 = "GATHER UNDERBREAST IN/ EX"
#         op2 = "Gather Underbust (Inside/Outside)"
#         score = get_similarity_score(op1, op2)
#         self.assertIsInstance(score, float)
#         self.assertGreaterEqual(score, 50)
#         self.assertLessEqual(score, 100)

#     def test_similarity_score_op3_op4(self):
#         op3 = "Attach Lining to Cup Sides"
#         op4 = "Top Stitch Neckline Elastic"
#         score = get_similarity_score(op3, op4)
#         self.assertIsInstance(score, float)
#         self.assertGreaterEqual(score, 0)
#         self.assertLessEqual(score, 50)

#     def test_similarity_score_mc1_mc2(self):
#         mc1 = "Lockstitch Auto Tack Machine"
#         mc2 = "Normal Lockstitch Auto Tack  Machine"
#         score = get_similarity_score(mc1, mc2)
#         self.assertIsInstance(score, float)
#         self.assertGreaterEqual(score, 50)
#         self.assertLessEqual(score, 100)


# if __name__ == "__main__":
#     unittest.main()
