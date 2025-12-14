import numpy as np

def sign(x):
    if x > 0:
        return 1
    else:
        return -1

def generate_X_dot(X):
    return np.concatenate((np.ones((len(X),1),dtype=float),X), axis=1)

def predict_single_data(x_dot,w_dot):
    return sign(np.dot(x_dot,w_dot))

def predict(X_dot,w_dot):
    rs = []
    for x_dot in X_dot:
        rs.append(predict_single_data(x_dot,w_dot))
    return np.array(rs)

def update_w_dot(x_dot, w_dot, y, learning_rate):
    return w_dot + x_dot*y*learning_rate

def train_verbose(X, y, epochs, learning_rate):
    w_dot = np.zeros(len(X[0])+1)

    X_dot = generate_X_dot(X)

    error_history = []

    for epoch in range(epochs):
        # TODO:
        # - predict label of every point x_dot_i
        # - if this point is missclassified, update w_dot
        # - remember to append total missclassified points 
        #   to error_history in every epoch
        num_of_error = 0
        for i in range(len(X_dot)):
            if predict_single_data(X_dot[i],w_dot) != y[i]:
                w_dot = update_w_dot(X_dot[i],w_dot,y[i],learning_rate)
                num_of_error += 1
        error_history.append(num_of_error)
        return w_dot, error_history