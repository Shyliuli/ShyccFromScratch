fn add(int a, int b)->int{
    return a + b;
}

fn square(int x)->int{
    return x * x;
}

fn main()->int{
    int n = add(4, 5);

    return square(n);
}
