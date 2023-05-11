class DynamicPriorityQueue():
    """
    Dynamic priority queue from CSDN
    """

    def __init__(self):
        self.A = []  # 真实数据存储在一维数组中，每个节点[key, value], value代表优先级
        self.mapping = {}  # 存储每个节点在一维数组中的位置，字典每项：[key, position]

    def top(self):  # 返回队列头部元素 min
        if len(self.A) == 0:
            return None
        return self.A[0][0]

    def pop(self):  # 最小元素出队，同时调整队列
        self.A[0], self.A[-1] = self.A[-1], self.A[0]  # 将队头队尾交换
        key = self.A[0][0]
        del self.mapping[key]  # 字典中删除队头节点对应的项
        self.A.pop()  # 删除队尾
        self.siftDown_(0)  # 将新的队头shift down

    def siftUp_(self, i):  # 上浮操作，将优先级较低的节点上浮，用于队尾插入新的节点 或 手动降低某些节点的优先级后的调整
        l = len(self.A)
        # 如果当前节点优先级 < 父节点优先级
        while 0 < i < l and self.A[(i - 1) // 2][1] <= self.A[i][1]:
            # 将当前节点与父节点交换
            self.A[(i - 1) // 2], self.A[i] = self.A[i], self.A[(i - 1) // 2]
            self.mapping[self.A[i][0]] = i  # 更新A[i]新的位置
            self.mapping[self.A[(i-1)//2][0]] = (i-1)//2  # 更新A[(i-1)/2]新的位置
            i = (i - 1) // 2  # 继续遍历父节点
        return i

    def siftDown_(self, i):  # 下沉操作，将优先级较高的节点下沉，用于队头出队后队尾换到队头时 或 手动升高某些节点优先级后的调整
        l = len(self.A)
        while 2 * i + 1 < l:
            min_child, l_child, r_child = i, 2 * i + 1, 2 * i + 2
            # 确定左右孩子节点中优先级最小的节点
            if l_child < l and self.A[l_child][1] >= self.A[min_child][1]:
                min_child = l_child
            if r_child < l and self.A[r_child][1] >= self.A[min_child][1]:
                min_child = r_child
            # 如果当前节点优先级大于孩子节点，则交换，并更新mapping
            if min_child > i:
                self.A[i], self.A[min_child] = self.A[min_child], self.A[i]
                self.mapping[self.A[i][0]] = i   # 更新A[i]新的位置
                # 更新A[min_child]新的位置
                self.mapping[self.A[min_child][0]] = min_child
            else:
                break
            i = min_child

        return i

    def push(self, key, val):
        self.A.append([key, val])  # 追加新的节点
        self.mapping[key] = len(self.A) - 1  # 初始放到队尾的位置
        return self.siftUp_(len(self.A) - 1)  # 最终位置根据调整情况确定

    def getVal(self, key):  # 获取某个节点的优先级
        if key not in self.mapping:
            return -1
        else:
            pos = self.mapping[key]  # 先拿到这个节点的位置
            return self.A[pos][1]  # 再获取这个节点的优先级

    def setVal(self, key, val):  # 修改已有节点
        if key not in self.mapping:
            self.push(key, val)
        else:
            pos = self.mapping[key]
            self.A[pos][1] = val
            pos = self.siftUp_(pos)
            pos = self.siftDown_(pos)

    def remove(self, key):  # 删除已有节点
        if key in self.mapping:
            pos = self.mapping[key]
            self.A[pos], self.A[-1] = self.A[-1], self.A[pos]
            self.mapping[self.A[pos][0]] = pos   # 更新A[pos]新的位置
            self.A.pop()
            del self.mapping[key]
            pos = self.siftUp_(pos)
            pos = self.siftDown_(pos)

    def decay(self, decay):
        """
        LRB algorithm (Extension: Locality)
        """
        for x in self.A:
            if x[1] > 0:
                x[1] *= decay
