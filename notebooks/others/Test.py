nums = [3,3]
target = 6

# for x in range(0,len(nums)):
#     for y in range(0,len(nums)):
#         if x == y:
#             continue
#         elif nums[x] + nums[y] == target:
#             print([x,y])

# l = [x , y for x in range (0,len(nums))
#             for y in range(0,len(nums))
#                 if x != y and nums[x] +nums[y] == target]

# l = [[i,j] for i,x in enumerate(nums) for j,y in enumerate(nums) if x + y != target or i == j]
# # print(l)


# print(n)
def twoSum(nums, target):
    stored_index = 0
    stored_num = nums[stored_index]
    output = self.loop_through_nums(nums, target, stored_num, stored_index)
    # print("OUTPUT: ", output)
    return output

print(twoSum(nums,target))
